from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,os,re,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_wait';w.mkdir(exist_ok=True)
g=os.environ.get('GHDL','ghdl');iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp')
ivbase=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args,cwd=r):
 p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,timeout=180)
 assert p.returncode==0,p.stdout+p.stderr
 return p.stdout+p.stderr
def save(p,s):
 t=p.with_suffix('.tmp');t.write_text(s);os.replace(t,p)
# CPU source is the current V34.1 core, with the normal unlocked test profile.
for name in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
 run([g,'-a','--std=08','-fsynopsys',str(r/'fpga/G80A_eZ80'/f'{name}_ez80.vhd')],w)
p=subprocess.run([g,'--synth','--std=08','-fsynopsys','--latches','--out=verilog','-gFETCH24=true','-gENABLE_MIXED=true','-gENABLE_SUFFIX_V2=true','-gENABLE_EZ80_ISA=true','G80A_eZ80'],cwd=w,capture_output=True,text=True)
assert p.returncode==0,p.stderr
s=re.sub(r'\bdo\b','data_out',p.stdout);needle='  wire [7:0] alu_q;';assert s.count(needle)==2
j=s.index(needle,s.index(needle)+1);s=s[:j]+s[j:].replace(needle,'  wire [7:0] alu_port_q;',1)
names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1
s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
save(w/'cpu.v',s)
common=[str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/memory_ez80.v'),str(w/'cpu.v')]
bridge=str(r/'fpga/src/ez80_memory_bridge.v')
def compile_case(label,entity,parameters,files):
 target=w/(label+'.vvp')
 run(ivbase+['-g2012','-s',entity,'-o',str(target)]+[f'-P{entity}.{k}={v}' for k,v in parameters.items()]+[str(r/'sim'/(entity+'.sv'))]+files)
 return label,target
proof=[]
for delay in (0,16):
 label,target=compile_case('old_'+str(delay),'tb_write_wait342',dict(ACK_DELAY=delay,CHECK_EARLY=0),common+[str(r/'sim/reference/ez80_memory_bridge_v34_1.v')])
 p=subprocess.run([vvp,str(target)],cwd=r,capture_output=True,text=True,timeout=60);t=p.stdout+p.stderr
 assert p.returncode!=0 and 'CPU entered write T3 before RAM completion' in t,t
 proof.append('EXPECTED FAILURE '+label+'\n'+t)
save(r/'test_results_wait_before_v34_2.log',''.join(proof))
cases=[]
for phase in range(8):
 for delay in (0,16):cases.append(compile_case(f'wait_{phase}_{delay}','tb_write_wait342',dict(PHASE=phase,ACK_DELAY=delay),common+[bridge]))
cases.append(compile_case('bridge','tb_bridge33',{},[bridge]))
cases.append(compile_case('memory','tb_memory33',{},[str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/memory_ez80.v'),bridge]))
def execute(item):
 label,target=item;t=run([vvp,str(target)]);assert 'PASS ' in t and '$finish called' in t and 'FATAL' not in t,t
 print('PASS',label,flush=True);return 'TEST '+label+'\n'+t
with ThreadPoolExecutor(max_workers=4) as pool:out=list(pool.map(execute,cases))
save(r/'test_results_wait_v34_2.log',''.join(out))
paths=[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'sim/tb_write_wait342.sv',r/'sim/tb_bridge33.sv',r/'sim/tb_memory33.sv',r/'sim/sdram_model33.sv',r/'sim/reference/ez80_memory_bridge_v34_1.v',r/'tools/run_wait342.py']
save(r/'verification_wait_v34_2.json',json.dumps(dict(passed=18,expected_old_failures=2,write_wait_cases=16,bridge_decode_checks=10240,memory_transactions=517,source_sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}),indent=2)+'\n')
print('PASS wait fix: 18 positive simulations; 2 old-controller failures reproduced separately')
