from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_io2_r21';w.mkdir(exist_ok=True)
jobs=[(s,1,e)for s in(0,1)for e in(0,1,2)]+[(0,0,0)]
def run(q):
 s,x,e=q;label=f's{s}_x{x}_e{e}';v=w/(label+'.vvp')
 cmd=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_io2_r21','-o',str(v),f'-Ptb_io2_r21.STRESS={s}',f'-Ptb_io2_r21.EXTENDED={x}',f'-Ptb_io2_r21.EVENT={e}',str(r/'sim/tb_io2_r21.sv'),str(r/'verification/cpu_1.v')]
 a=subprocess.run(cmd,capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out);assert a.returncode==0 and'PASS IO2'in out,out
 print(out.strip(),flush=True);return dict(profile=q,cases=40 if x else 4,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,jobs))
(r/'verification_io2_r21_result.json').write_text(json.dumps(dict(fresh_runs=sum(x['cases']for x in rows),profiles=rows,flat_RAM=True,GOWIN_tested=False),indent=2)+'\n')
