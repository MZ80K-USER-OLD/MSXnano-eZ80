"""Reproduce v33 memory verification. Requires GHDL, Icarus Verilog, Python3."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,re,shutil,subprocess,time,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
work=r/'verification_memory';work.mkdir(exist_ok=True)
synth=r/'verification_synth';synth.mkdir(exist_ok=True)
ghdl=os.environ.get('GHDL','ghdl');iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp')
ivbase=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args,cwd=r,timeout=240):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(str(args)+'\n'+p.stdout+'\n'+p.stderr)
 return p.stdout+p.stderr
def save(path,text):
 tmp=path.with_suffix('.tmp');tmp.write_text(text);os.replace(tmp,path)
started=time.monotonic()
run(['python3','tools/make_cpu_image33.py'])
for name in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
 run([ghdl,'-a','--std=08','-fsynopsys',str(r/'fpga/G80A_eZ80'/f'{name}_ez80.vhd')],synth)
p=subprocess.run([ghdl,'--synth','--std=08','-fsynopsys','--out=verilog',
 '-gFETCH24=true','-gENABLE_MIXED=true','-gENABLE_SUFFIX_V2=true','-gENABLE_EZ80_ISA=true','G80A_eZ80'],cwd=synth,text=True,capture_output=True)
assert p.returncode==0,p.stderr
save(r/'test_results_cpu_conversion_v33.log',p.stderr+'PASS GHDL CPU synthesis for simulation (not Gowin)\n')
# GHDL's Verilog emitter uses a SystemVerilog keyword and collides the ALU
# output's generated net name with the VHDL signal name. Rename only emitted
# identifiers; all six VHDL sources remain byte-identical to published v32.
s=re.sub(r'\bdo\b','data_out',p.stdout)
needle='  wire [7:0] alu_q;';assert s.count(needle)==2
j=s.index(needle,s.index(needle)+1)
s=s[:j]+s[j:].replace(needle,'  wire [7:0] alu_port_q;',1)
assert s.count('assign alu_n435 = alu_q;')==1 and s.count('.q(alu_q)')==1
s=s.replace('assign alu_n435 = alu_q;','assign alu_n435 = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
save(synth/'cpu_netlist.v',s)
common=[str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
tasks=[]
def compile_case(entity,label,parameters,files):
 target=work/(label+'.vvp')
 run(ivbase+['-g2012','-s',entity,'-o',str(target)]+[f'-P{entity}.{k}={v}' for k,v in parameters.items()]+[str(r/'sim'/(entity+'.sv'))]+files)
 tasks.append((label,target))
compile_case('tb_bridge33','bridge',{},[common[0]])
for phase in range(16):
 compile_case('tb_memory33',f'memory_{phase}',{'PHASE':phase},[str(r/'sim/sdram_model33.sv')]+common)
for phase in range(8):
 compile_case('tb_cpu_memory33',f'cpu_{phase}',{'PHASE':phase},[str(r/'sim/sdram_model33.sv'),str(synth/'cpu_netlist.v')]+common)
for phase in range(4):
 compile_case('tb_memory_compat33',f'compat_{phase}',{'PHASE':phase},[str(r/'fpga/src/memory.v'),common[1]])
# Full power-on delay is exercised once; other cases skip only that long delay.
compile_case('tb_memory33','power_on',{'SKIP_INIT':0},[str(r/'sim/sdram_model33.sv')]+common)
def execute(item):
 label,path=item;output=run([vvp,str(path)],timeout=300)
 assert 'PASS ' in output and '$finish called' in output and 'FATAL' not in output,output
 print('PASS',label,flush=True)
 return label,output
with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(execute,tasks))
for label,output in results:save(work/(label+'.log'),output)
save(r/'test_results_memory_v33.log',''.join('TEST '+label+'\n'+output for label,output in results))
# Check changed Verilog. Peripheral HDL uses constructs outside Icarus support;
# it, VHDL and vendor primitives are black boxes. This is not full elaboration.
files=[str(r/'fpga/top_ez80.v')]+common
output=run(ivbase+['-g2012','-i','-tnull','-s','top','-I',str(r/'fpga/src')]+files,r/'fpga')
save(r/'test_results_top_syntax_v33.log',output+'PASS changed Verilog syntax; peripherals/VHDL/vendor modules blackboxed\n')
manifest=dict(version=33,fresh_simulation_runs=len(results),bridge_decode_checks=10240,
 memory_runs=16,memory_transactions_per_run=517,cpu_integration_runs=8,
 legacy_pin_comparison_runs=4,power_on_runs=1,power_on_transactions=518,
 inherited_v32_cpu_executions=25361,inherited_cpu_tests_rerun=False,
 cpu_conversion='GHDL synth to Verilog; emitted identifier cleanup only',
 top_syntax='Icarus changed files only: peripherals/VHDL/vendor modules blackboxed',
 gowin_tested=False,hardware_tested=False,
 source_sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
 list((r/'fpga/G80A_eZ80').glob('*.vhd'))+[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'fpga/top_ez80.v']},
 test_source_sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
 list((r/'sim').glob('*33.sv'))+[r/'tools/make_cpu_image33.py',r/'tools/run_memory33.py']+list((r/'sim/image33').glob('*'))})
save(r/'verification_result_v33.json',json.dumps(manifest,indent=2)+'\n')
print('PASS v33:',len(results),'fresh simulation runs; complete logs saved',flush=True)
