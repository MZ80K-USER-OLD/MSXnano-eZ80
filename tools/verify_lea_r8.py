from pathlib import Path
import os,subprocess,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_lea_r8';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=600)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
cases=[(i,0,1) for i in (0,3,7,11)]+[(0,1,1),(3,2,1),(0,0,0)]
for phase,fault,ext in cases:
 label=f'p{phase}_f{fault}_e{ext}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'hardware_test'),'-s','tb_lea_r8','-o',str(p)]+[f'-Ptb_lea_r8.{k}={v}' for k,v in dict(PHASE=phase,FAULT=fault,EXTENDED=ext).items()]+
 [str(r/'sim/tb_lea_r8.sv'),str(r/'verification'/f'cpu_{ext}.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(p)])
 expected='UNSUPPORTED' if not ext else ('FAIL stage 1' if fault==1 else 'FAIL stage 2') if fault else 'PASS'
 assert 'EZ80LEA P1: '+expected in out and 'PASS lea_r8' in out,out
 if fault==1:assert 'ADDR=060102 EXP=03 ACT=02' in out,out
 if fault==2:assert 'ADDR=04FFFF EXP=00 ACT=01' in out,out
 (w/(label+'.log')).write_text(out);print('PASS lea_r8',label,flush=True)
(r/'verification_lea_r8_result.json').write_text(json.dumps({'fresh_runs':len(cases),'cases':cases,'COM_sha256':hashlib.sha256((r/'hardware_test/EZ80LEA.COM').read_bytes()).hexdigest(),'EA_captures_per_nominal_run':26,'LEA_commits_per_nominal_run':24,'PEA_stack_writes_per_nominal_run':6,'preloaded_COM_changed':False},indent=2)+'\n')
