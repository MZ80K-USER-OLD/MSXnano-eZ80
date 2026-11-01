from pathlib import Path
import os,subprocess,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_alu_r5';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,capture_output=True,text=True,timeout=600)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
cases=[(phase,0,1) for phase in (0,3,7,11)]+[(0,1,1),(0,0,0)]
for phase,fault,ext in cases:
 label=f'p{phase}_f{fault}_e{ext}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'hardware_test'),'-s','tb_alu_r5','-o',str(p)]+[f'-Ptb_alu_r5.{k}={v}' for k,v in dict(PHASE=phase,FAULT=fault,EXTENDED=ext).items()]+
     [str(r/'sim/tb_alu_r5.sv'),str(r/'verification'/f'cpu_{ext}.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(p)])
 expected='UNSUPPORTED' if not ext else 'FAIL stage 1' if fault else 'PASS'
 assert 'EZ80ALU P1: '+expected in out and 'PASS alu_r5' in out,out
 if fault:assert 'ADDR=060102 EXP=01 ACT=00' in out,out
 (w/(label+'.log')).write_text(out);print('PASS alu_r5',label,flush=True)
(r/'verification_alu_r5_result.json').write_text(json.dumps({'fresh_runs':len(cases),'cases':cases,'arithmetic_cases_per_nominal_run':24,'preloaded_COM_changed':False,'COM_sha256':hashlib.sha256((r/'hardware_test/EZ80ALU.COM').read_bytes()).hexdigest(),'gowin_tested':False,'hardware_tested':False},indent=2)+'\n')
