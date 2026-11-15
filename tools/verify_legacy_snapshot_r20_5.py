from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_legacy_snapshot_r20_5';w.mkdir(exist_ok=True)
jobs=[(p,f,0,n)for p in range(4)for f in (0,1)for n in(0,1)]+[(0,1,1,1)]
def run(q):
 p,f,reset,neg=q;label=f'p{p}_f{f}_r{reset}_n{neg}';v=w/(label+'.vvp')
 cmd=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_legacy_snapshot_r20_5','-o',str(v),f'-Ptb_legacy_snapshot_r20_5.PHASE={p}',f'-Ptb_legacy_snapshot_r20_5.POISON={f}',f'-Ptb_legacy_snapshot_r20_5.RESET_CASE={reset}',f'-Ptb_legacy_snapshot_r20_5.LAUNCH_NEG={neg}']+[str(r/n)for n in ['sim/tb_legacy_snapshot_r20_5.sv','sim/sdram_model33.sv','fpga/src/memory_ez80.v']]
 a=subprocess.run(cmd,capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=180);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 assert a.returncode==0 and 'PASS legacy_snapshot'in out,out
 print(out.strip(),flush=True);return dict(profile=q,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,jobs))
(r/'verification_legacy_snapshot_r20_5_result.json').write_text(json.dumps(dict(fresh_runs=len(rows),cases=rows,physical_failure_reproduced=False,post_capture_payload_perturbed=True,mapper_and_megaram_write_read_and_priority=True),indent=2)+'\n')
