"""Validate the two GPRJs, the observer-only boundary, and UART behavior."""
from pathlib import Path
import hashlib,json,os,re,subprocess,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent;host=r.parents[1]
w=r/'verification_uart_profiles_r24_5';w.mkdir(exist_ok=True)
iv=[os.environ.get('IVERILOG',str(host/'local-iverilog/usr/bin/iverilog')if(host/'local-iverilog/usr/bin/iverilog').exists()else'iverilog')]
ivroot=os.environ.get('IVL_ROOT',str(host/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'))
if Path(ivroot).exists():iv+=['-B',ivroot]
vvp=os.environ.get('VVP',str(host/'local-iverilog/usr/bin/vvp')if(host/'local-iverilog/usr/bin/vvp').exists()else'vvp')
profiles={
 'normal':r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',
 'diagnostic':r/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj'}
files={}
for profile,project in profiles.items():
 files[profile]=[(project.parent/e.attrib['path']).resolve()for e in ET.parse(project).iter()if e.tag=='File']
 assert len(files[profile])==123 and all(p.is_file()for p in files[profile])
 assert sum(p.name in {'msx2p_debug.v','msx2p_debug_disabled.v'}for p in files[profile])==1
assert set(files['normal'])^set(files['diagnostic'])=={(r/'fpga/src/msx2p_debug.v').resolve(),(r/'fpga/src/msx2p_debug_disabled.v').resolve()}
top=(r/'fpga/top_ez80.v').read_text()
block=re.search(r'\bmsx2p_debug\s+debug\s*\((.*?)\);',top,re.S).group(1)
assert re.search(r'\.boot_ok\s*\(\s*\)',block)
assert re.search(r'\.uart_tx\s*\(uart_tx\)',block)
assert '.DIAGNOSTICS (EZ80_EXTENDED)'in top
stub=(r/'fpga/src/msx2p_debug_disabled.v').read_text()
assert 'always'not in stub and 'reg 'not in stub and 'assign uart_tx = 1\'b1;'in stub
# Icarus lacks the streaming-concatenation syntax used by the existing logger.
# Every print argument is a packed vector or string. A streaming argument
# feeds the 1024-bit task input from its MSB end and pads on the right.
# Preserve that alignment explicitly in a simulation-only include copy.
compat=w/'include';compat.mkdir(exist_ok=True)
original_print=(r/'fpga/src/print.v').read_text()
assert original_print.count('{>>{a}}')==1
(compat/'print.v').write_text(original_print.replace('{>>{a}}',"{a, {(1024-$bits(a)){1'b0}}}"))
results=[]
for profile,project in profiles.items():
 selected=next(p for p in files[profile]if p.name in{'msx2p_debug.v','msx2p_debug_disabled.v'})
 p=w/(profile+'.vvp')
 cmd=iv+['-g2012','-I',str(compat),'-s','tb_uart_profiles_r24_5',f'-Ptb_uart_profiles_r24_5.DIAGNOSTIC={int(profile=="diagnostic")}','-o',str(p),str(r/'sim/tb_uart_profiles_r24_5.sv'),str(selected),str(r/'fpga/src/uart_tx.v')]
 a=subprocess.run(cmd,cwd=r,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([vvp,str(p)],cwd=r,capture_output=True,text=True,timeout=60);out=a.stdout+a.stderr;(w/(profile+'.log')).write_text(out)
 assert not a.returncode and 'PASS UART '+profile in out,out
 print(out.strip(),flush=True)
 # Check the selected source list through preprocessing. Existing SD/HDMI RTL
 # uses GOWIN constructs that Icarus cannot fully elaborate, so the subsequent
 # syntax check is explicitly limited to top + selected observer + UART.
 verilogs=[str(p)for p in files[profile]if p.suffix in{'.v','.sv'}]
 cmd=iv+['-g2012','-E','-o',str(w/(profile+'_preprocessed.v')),'-I',str(r/'fpga/src')]+verilogs
 a=subprocess.run(cmd,cwd=r,capture_output=True,text=True,timeout=60);assert not a.returncode,a.stdout+a.stderr
 cmd=iv+['-g2012','-i','-tnull','-I',str(compat),'-I',str(r/'fpga/src'),'-s','top',str(r/'fpga/top_ez80.v'),str(selected),str(r/'fpga/src/uart_tx.v')]
 a=subprocess.run(cmd,cwd=r,capture_output=True,text=True,timeout=60);(w/(profile+'_verilog.log')).write_text(a.stdout+a.stderr)
 assert not a.returncode,a.stdout+a.stderr
 results.append(dict(profile=profile,selected_module=str(selected.relative_to(r)),project_sources=123,UART_simulation='PASS',selected_Verilog_preprocessing='PASS',top_plus_logger_syntax_with_other_modules_unresolved='PASS',full_board_elaboration=False))
# Tcl syntax/control-flow check with mocked GOWIN commands. This does not
# establish that this machine has run GOWIN or saved its IDE preferences.
tcl='''proc open_project {path} {if {![file exists $path]} {error "missing GPRJ"};set ::opened $path}
proc set_option {name value} {dict set ::options $name $value}
proc run {phase} {if {$phase ne "all"} {error "bad build phase"};set ::ran 1}
'''
for profile in profiles:
 script=r/'fpga'/('configure_'+profile+'.tcl')
 runscript=r/'fpga'/('build_'+profile+'.tcl')
 test=tcl+'\nsource {'+str(script)+'}\n'
 test+='if {[dict get $::options -verilog_std] ne "sysv2017" || [dict get $::options -vhdl_std] ne "vhd1993"} {error "language mismatch"}\n'
 test+='if {[dict get $::options -use_mspi_as_gpio] != 1 || [dict get $::options -use_sspi_as_gpio] != 1} {error "dual pin mismatch"}\n'
 test+='if {[dict get $::options -use_jtag_as_gpio] != 0} {error "JTAG mismatch"}\n'
 test+='source {'+str(runscript)+'}\nif {!$::ran} {error "no build requested"}\nputs "PASS Tcl '+profile+'"\n'
 p=w/(profile+'_tcl_test.tcl');p.write_text(test)
 a=subprocess.run(['tclsh',str(p)],cwd=r,capture_output=True,text=True);(w/(profile+'_tcl.log')).write_text(a.stdout+a.stderr)
 assert not a.returncode,a.stdout+a.stderr
result=dict(profiles=results,real_UART_divider_tested=True,simulation_scheduler_accelerated=True,simulation_only_streaming_compatibility=True,Tcl_mock_tests='PASS',GOWIN=False,board=False,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in set(files['normal'])|set(files['diagnostic'])})
(w/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS both project selections, UART behavior, preprocessing, top/logger syntax, and Tcl mock checks')
