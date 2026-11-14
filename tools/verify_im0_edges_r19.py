from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_im0_edges_r19';w.mkdir(exist_ok=True)
iv=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT']]
jobs=[(c,s,h,n,0) for c in range(3) for s in (0,1) for h,n in [(1,0),(0,1),(0,2)]]+[(0,0,0,0,1)]
def run(q):
 c,s,h,n,f=q;label='_'.join(map(str,q));v=w/(label+'.vvp')
 params={'CTX':c,'STRESS':s,'CPU_DIV':15 if s else 4,'FAULT':f,'HALT_SRC':h,'NMI_RACE':int(n==1),'NMI_DURING':int(n==2)}
 a=subprocess.run(iv+['-g2012','-s','tb_im0_r19','-o',str(v)]+[f'-Ptb_im0_r19.{k}={x}' for k,x in params.items()]+[str(r/'sim/tb_im0_r19.sv'),str(r/'verification/cpu_1.v')],text=True,capture_output=True);assert a.returncode==0,a.stderr
 for op in ([199] if f else [199,255,205,118]):
  a=subprocess.run([os.environ['VVP'],str(v),'+OP='+str(op)],text=True,capture_output=True,timeout=120)
  out=a.stdout+a.stderr;(w/(label+'_'+str(op)+'.log')).write_text(out)
  if f:assert a.returncode!=0 and 'IM0 frame write' in out,out
  else:assert a.returncode==0 and 'PASS IM0 matrix cases=1' in out,out[-1800:]
 print('PASS IM0 edge profile',q,flush=True);return {'profile':q,'fresh_runs':0 if f else 4,'expected_failure_runs':int(f)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,jobs))
(r/'verification_im0_edges_r19_result.json').write_text(json.dumps({'fresh_runs':sum(x['fresh_runs'] for x in rows),'expected_failure_runs':sum(x['expected_failure_runs'] for x in rows),'cases':rows},indent=2)+'\n')
