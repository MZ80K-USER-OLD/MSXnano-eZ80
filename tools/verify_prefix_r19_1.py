from pathlib import Path
import subprocess,os,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_prefix_r19_1';w.mkdir(exist_ok=True)
iv=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT']]
jobs=[(0,0,s,0) for s in (0,1)]+[(e,i,s,0) for e in (1,2) for i in range(5) for s in (0,1)]+[(0,0,0,1)]
if os.environ.get('SMOKE'):jobs=[(0,0,0,0),(1,0,0,0),(2,4,1,0),(0,0,0,1)]
def run(q):
 e,i,s,f=q;label='_'.join(map(str,q));v=w/(label+'.vvp')
 params={'EVENT':e,'INJECT':i,'STRESS':s,'CPU_DIV':15 if s else 4,'FAULT':f}
 a=subprocess.run(iv+['-g2012','-s','tb_prefix_r19_1','-o',str(v)]+[f'-Ptb_prefix_r19_1.{k}={x}' for k,x in params.items()]+[str(r/'sim/tb_prefix_r19_1.sv'),str(r/'verification/cpu_1.v')],capture_output=True,text=True);assert a.returncode==0,a.stderr
 extra=['+CASE=0'] if f else ['+CASE=400'] if os.environ.get('SMOKE') else []
 a=subprocess.run([os.environ['VVP'],str(v)]+extra,capture_output=True,text=True,timeout=1800)
 out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 if f:assert a.returncode!=0 and 'PREFIX data' in out,out
 else:assert a.returncode==0 and 'PASS PREFIX matrix cases=' in out,out[-2200:]
 n=0 if f else 1 if extra else 496 if e==0 else 48
 print('PASS prefix profile',q,n,flush=True)
 return {'profile':q,'fresh_runs':n,'expected_failure_runs':int(f)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,jobs))
p=r/('verification_prefix_r19_1_smoke_result.json' if os.environ.get('SMOKE') else 'verification_prefix_r19_1_result.json')
p.write_text(json.dumps({'fresh_runs':sum(x['fresh_runs'] for x in rows),'expected_failure_runs':sum(x['expected_failure_runs'] for x in rows),'profiles':rows,'documented_memory_CB_forms':31,'all_four_suffixes':True,'DD_and_FD':True,'source_modes':2,'IRQ_NMI_injection_points':5,'flat_RAM':True,'physical_timing_verified':False},indent=2)+'\n')
