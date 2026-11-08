from pathlib import Path
import os,json,hashlib,subprocess,concurrent.futures,shutil
r=Path(__file__).resolve().parent.parent;w=r/'verification_mixed_r14';w.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'sim/build_mixed_r14.py')],check=True)
shutil.copyfile(r/'verification/cpu_1.v',w/'cpu_snapshot.v')
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
ids=list(range(64)) if not os.environ.get('CASES') else [int(x) for x in os.environ['CASES'].split(',')]
profiles=[(4,0,0)] if os.environ.get('SMOKE') else [(4,0,0),(4,1,3),(16,1,11)]
cases=[(c,d,s,p,0) for c in ids for d,s,p in profiles]+[(0,4,0,0,1),(0,4,0,0,2)]
def run(q):
 c,d,s,p,f=q;label=f'c{c}_d{d}_s{s}_p{p}_f{f}';v=w/(label+'.vvp')
 a=subprocess.run(base+['-g2012','-I',str(r/'sim'),'-s','tb_mixed_r14','-o',str(v)]+[f'-Ptb_mixed_r14.{k}={v}' for k,v in dict(CASE=c,CPU_DIV=d,STRESS=s,PHASE=p,FAULT=f).items()]+[str(r/'sim/tb_mixed_r14.sv'),str(w/'cpu_snapshot.v')],capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([vvp,str(v)],capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 if f:assert a.returncode!=0 and 'frame write' in out,out
 else:assert a.returncode==0 and 'PASS mixed_r14' in out,out
 print('PASS MIXED',q,flush=True);return dict(case=q,result=out[-900:])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
j=dict(fresh_runs=len(ids)*len(profiles),expected_failure_runs=2,cases=rows,logical_flat_RAM=True,not_board_mapping=True,mixed_CALL_RET_conditions_and_frames=True,shared_MADL_engine=True,frame_wait_CEN_and_bus_request_checks=True,pending_NMI_during_CALL_and_IRQ_during_RET=True,RET_L_LIS_LIL_layouts=True,caller_width_mismatch_and_bad_mode_guard=True,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')})
(r/'verification_mixed_r14_result.json').write_text(json.dumps(j,indent=2)+'\n')
