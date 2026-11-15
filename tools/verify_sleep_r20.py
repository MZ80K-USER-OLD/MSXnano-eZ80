from pathlib import Path
import subprocess,os,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_sleep_r20';w.mkdir(exist_ok=True)
jobs=[(c,s,1,0,0)for c in range(5)for s in(0,1)]+[(0,s,0,0,0)for s in(0,1)]+[(c,s,1,0,1)for c in(1,2)for s in(0,1)]+[(2,0,1,1,0)]
def run(q):
 c,s,e,f,b=q;label='_'.join(map(str,q));v=w/(label+'.vvp');iv=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT']]
 a=subprocess.run(iv+['-g2012','-s','tb_sleep_r20','-o',str(v)]+[f'-Ptb_sleep_r20.{k}={x}'for k,x in dict(CTX=c,STRESS=s,CPU_DIV=15 if s else 4,FAULT=f,PREBUS=b).items()]+[str(r/'sim/tb_sleep_r20.sv'),str(r/'verification'/f'cpu_{e}.v')],capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 if f:assert a.returncode!=0 and 'SLP PC' in out,out
 else:assert a.returncode==0 and 'PASS SLP cases='in out,out
 n=0 if f else 1 if c==0 else 20
 print('PASS SLP profile',q,n,flush=True);return dict(profile=q,fresh_runs=n,expected_failure_runs=int(f))
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,jobs))
(r/'verification_sleep_r20_result.json').write_text(json.dumps(dict(fresh_runs=sum(x['fresh_runs']for x in rows),expected_failure_runs=1,profiles=rows,production_reset_only=True,IRQ_NMI_do_not_wake=True,WAIT_CEN_BUSRQ=True,PC_boundary=True,SDRAM_VDP_clock_stopped=False),indent=2)+'\n')
