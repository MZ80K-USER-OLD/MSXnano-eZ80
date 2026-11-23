from pathlib import Path
import subprocess,concurrent.futures,os,json,hashlib
r=Path(__file__).resolve().parents[1];w=r/'verification_tstio_r25';w.mkdir(exist_ok=True)
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']]if os.environ.get('IVL_ROOT')else[])
vvp=os.environ.get('VVP','vvp')
subprocess.run(['python3',str(r/'sim/build_tstio_r25.py')],check=True)
cases=[(0,0),(0,1),(1,0),(1,1),(2,0),(2,1),(3,1),(4,1),(5,1),(6,1)]
def run(q):
 c,s=q;label=f'case{c}_stress{s}';v=w/(label+'.vvp')
 cmd=iv+['-g2012','-I',str(r/'sim'),'-s','tb_tstio_r25',f'-Ptb_tstio_r25.CASE={c}',f'-Ptb_tstio_r25.STRESS={s}',f'-Ptb_tstio_r25.PHASE={3 if s else 0}','-o',str(v),str(r/'sim/tb_tstio_r25.sv'),str(r/'verification/cpu_1.v')]
 p=subprocess.run(cmd,cwd=r,capture_output=True,text=True);assert not p.returncode,p.stderr
 p=subprocess.run([vvp,str(v)],cwd=r,capture_output=True,text=True,timeout=600);out=p.stdout+p.stderr;(w/(label+'.log')).write_text(out)
 assert not p.returncode and 'PASS tstio_r25'in out,out
 print(out.strip(),flush=True);return dict(case=c,stress=s,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
(w/'result.json').write_text(json.dumps({'cases':rows,'GOWIN':False,'board':False,'source_SHA256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(r/'fpga/G80A_eZ80').glob('*.vhd')}},indent=2)+'\n')
