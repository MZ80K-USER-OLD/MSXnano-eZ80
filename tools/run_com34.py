"""Execute the shipped COM with the real CPU fork, bridge and SDRAM model."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,re,subprocess
r=Path(__file__).resolve().parent.parent
work=r/'verification_com';work.mkdir(exist_ok=True)
ghdl=os.environ.get('GHDL','ghdl');iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp')
ivbase=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args,cwd=r,timeout=600):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(str(args)+'\n'+p.stdout+'\n'+p.stderr)
 return p.stdout+p.stderr
def save(p,text):
 t=p.with_suffix('.tmp');t.write_text(text);os.replace(t,p)
print(run(['python3','hardware_test/build_ram34.py']),end='',flush=True)
conversion=[]
for extended in (True,False):
 cwd=work/('enabled' if extended else 'compat');cwd.mkdir(exist_ok=True)
 for name in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
  run([ghdl,'-a','--std=08','-fsynopsys',str(r/'fpga/G80A_eZ80'/f'{name}_ez80.vhd')],cwd)
 args=[ghdl,'--synth','--std=08','-fsynopsys','--out=verilog']+([] if extended else ['--latches'])+[f'-g{x}={str(extended).lower()}' for x in ('FETCH24','ENABLE_MIXED','ENABLE_SUFFIX_V2','ENABLE_EZ80_ISA','BOOT_Z80_COMPAT')]+['G80A_eZ80']
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True);assert p.returncode==0,p.stderr
 # Identifier cleanup for GHDL-generated Verilog only, as in V33.
 s=re.sub(r'\bdo\b','data_out',p.stdout)
 needle='  wire [7:0] alu_q;'
 if s.count(needle)==2:
  j=s.index(needle,s.index(needle)+1);s=s[:j]+s[j:].replace(needle,'  wire [7:0] alu_port_q;',1)
  names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1,names
  s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
 save(cwd/'cpu.v',s);conversion.append(f'PROFILE extended={extended}\n'+p.stderr)
save(r/'test_results_cpu_conversion_v34_2.log',''.join(conversion)+'PASS GHDL conversion of both CPU profiles (not Gowin synthesis)\n')
cases=[dict(label=f'nominal_{phase}',PHASE=phase,CPU_DIV=16,FAULT=0,EXTENDED=1) for phase in (0,7)]
cases += [dict(label='alias_fault',PHASE=7,CPU_DIV=16,FAULT=1,EXTENDED=1),
          dict(label='copy_fault',PHASE=0,CPU_DIV=16,FAULT=2,EXTENDED=1),
          dict(label='unsupported',PHASE=0,CPU_DIV=16,FAULT=0,EXTENDED=0)]
common=[str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
for case in cases:
 profile='enabled' if case['EXTENDED'] else 'compat'
 run(ivbase+['-g2012','-I',str(r/'hardware_test'),'-s','tb_com34','-o',str(work/(case['label']+'.vvp'))]+
     [f'-Ptb_com34.{k}={v}' for k,v in case.items() if k!='label']+
     [str(r/'sim/tb_com34.sv'),str(work/profile/'cpu.v')]+common)
def execute(case):
 output=run([vvp,str(work/(case['label']+'.vvp'))])
 expected='EZ80RAM: UNSUPPORTED' if not case['EXTENDED'] else ('EZ80RAM: FAIL stage '+('1' if case['FAULT']==1 else 'C')) if case['FAULT'] else 'EZ80RAM: PASS'
 assert expected in output and 'PASS com34 ' in output and '$finish called' in output and 'FATAL' not in output,output
 if case['FAULT']==2:
  info=json.loads((r/'hardware_test/EZ80RAM_v34.json').read_text())
  for field in [f"SRC={info['labels']['PAYLOAD']:04X}",'DST=010000','EXP=31','READ=30','RETRY=30','ABS=30','LEFT=0201']:
   assert field in output,(field,output)
 save(work/(case['label']+'.log'),output);print('PASS',case['label'],flush=True)
 return 'TEST '+json.dumps(case)+'\n'+output
with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(execute,cases))
save(r/'test_results_com_v34_2.log',''.join(records))
output=run(ivbase+['-g2012','-i','-tnull','-s','top','-I',str(r/'fpga/src'),str(r/'fpga/top_ez80.v')]+common[1:],r/'fpga')
save(r/'test_results_top_syntax_v34_2.log',output+'PASS changed Verilog syntax; peripherals/VHDL/vendor modules blackboxed\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=list((r/'fpga/G80A_eZ80').glob('*.vhd'))+[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'fpga/top_ez80.v']
tests=[r/'sim/tb_com34.sv',r/'sim/sdram_model33.sv',r/'hardware_test/build_ram34.py',r/'tools/run_com34.py']+list((r/'hardware_test').glob('*34.*'))+[r/'hardware_test/EZ80RAM.COM',r/'hardware_test/EZ80RAM.hex']
m=dict(version='34.2',fresh_simulation_runs=len(cases),cases=cases,nominal_cpu_divisor=16,
 actual_com_executed=True,full_msx_dos_simulated=False,bdos='function 9 Z80 stub plus DOS-style caller',
 injected_faults='data-bank alias and first copied byte corruption, both return FAIL to DOS caller',
 inherited_v33_memory_runs=30,inherited_v32_cpu_runs=25361,inherited_tests_rerun=False,
 gowin_tested=False,hardware_tested=False,default_EZ80_EXTENDED=1,
 source_sha256={str(p.relative_to(r)):sha(p) for p in paths},test_source_sha256={str(p.relative_to(r)):sha(p) for p in set(tests)})
save(r/'verification_result_v34_2.json',json.dumps(m,indent=2)+'\n')
print('PASS V34.2:',len(cases),'COM execution scenarios and partial top syntax; logs saved',flush=True)
