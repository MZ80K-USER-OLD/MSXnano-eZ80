from pathlib import Path
import subprocess,os,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_ior_r22';w.mkdir(exist_ok=True)
iv=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT']]
cases=[(s,1,e,0)for s in(0,1)for e in(0,1,2)]+[(0,0,0,0)]+[(s,1,1,1)for s in(0,1)]
def run(c):
 s,x,e,b=c;top='tb_ior_boundary_r22'if b else'tb_ior_r22';v=w/('_'.join(map(str,c))+'.vvp');cmd=iv+['-g2012','-s',top,'-o',str(v),f'-P{top}.STRESS={s}',f'-P{top}.EXTENDED={x}',f'-P{top}.EVENT={e}',str(r/'sim'/(top+'.sv')),str(r/'verification/cpu_1.v')]
 p=subprocess.run(cmd,capture_output=True,text=True);assert not p.returncode,p.stderr
 p=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=300);out=p.stdout+p.stderr;v.with_suffix('.log').write_text(out);assert not p.returncode and 'PASS IOR' in out,out
 print(out.strip(),flush=True);return dict(profile=c,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
(w/'result.json').write_text(json.dumps(dict(profiles=rows,cases=648,GOWIN=False,hardware=False),indent=2))
