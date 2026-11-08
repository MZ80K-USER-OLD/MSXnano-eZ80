from pathlib import Path
import os,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_control_r10';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=600)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
cases=[(i,0,1,1,16,0) for i in (0,3,7,11)]+[(0,1,1,1,16,0),(0,0,0,1,16,0),(0,0,1,0,16,0),(3,0,1,1,4,0),(7,0,1,1,4,1)]
def check(q):
 phase,fault,ext,request,div,pause=q
 label=f'p{phase}_f{fault}_e{ext}_r{request}_d{div}_pause{pause}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s','tb_control_r10','-o',str(p)]+[f'-Ptb_control_r10.{k}={v}' for k,v in dict(PHASE=phase,FAULT=fault,EXTENDED=ext,RUN_REQUEST=request,CPU_DIV=div,PAUSE_ENABLE=pause).items()]+
 [str(r/'sim/tb_control_r10.sv'),str(r/'verification'/f'cpu_{ext}.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(p)])
 expected='READY' if not request else 'UNSUPPORTED' if not ext else 'FAIL stage C' if fault else 'PASS'
 assert 'EZ80CTL R10: '+expected in out and 'PASS control_r10' in out,out
 if fault==1:assert 'ADDR=030200 EXP=22 ACT=23' in out,out
 (w/(label+'.log')).write_text(out);print('PASS control_r10',label,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(check,cases))
(r/'verification_control_r10_result.json').write_text(json.dumps({'fresh_runs':len(cases),'cases':cases,'COM_sha256':hashlib.sha256((r/'hardware_test/EZ80CTL.COM').read_bytes()).hexdigest(),'ADL_payloads_per_nominal_run':1,'new_COM':True},indent=2)+'\n')
