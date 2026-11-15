from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_refresh_r20_1';w.mkdir(exist_ok=True)
def run(q):
 p,l,f=q;name=f'p{p}_l{l}_f{f}';v=w/(name+'.vvp');a=subprocess.run([os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_refresh_r20_1','-o',str(v)]+[f'-Ptb_refresh_r20_1.{k}={x}'for k,x in dict(PHASE=p,LONG_RUN=l,FAULT=f).items()]+[str(r/'sim/tb_refresh_r20_1.sv'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/memory_ez80.v')],capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=1200);out=a.stdout+a.stderr;(w/(name+'.log')).write_text(out)
 if f:assert a.returncode!=0 and 'REFRESH missing' in out,out
 else:assert a.returncode==0 and 'PASS refresh' in out,out
 print('PASS refresh',q,flush=True);return dict(profile=q,output=out)
jobs=[(p,0,0)for p in(0,1,2,3)]+[(0,1,0),(0,0,1)]
if os.environ.get('SMOKE'):jobs=jobs[:1]
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(run,jobs))
(r/'verification_refresh_r20_1_result.json').write_text(json.dumps(dict(fresh_runs=len(rows)-int(not os.environ.get('SMOKE')),expected_failure_runs=int(not os.environ.get('SMOKE')),cases=rows,clock_MHz=100,physical_retention_measured=False),indent=2)+'\n')
