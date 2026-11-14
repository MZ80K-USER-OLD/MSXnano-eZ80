from pathlib import Path
import os,json,hashlib,subprocess,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_madl_r13';w.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'sim/build_madl_r13.py')],check=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
ids=list(range(26)) if not os.environ.get('CASES') else [int(x) for x in os.environ['CASES'].split(',')]
profiles=[(4,0,0)] if os.environ.get('SMOKE') else [(4,0,0),(4,1,3),(16,1,11)]
cases=[(c,d,s,p,0) for c in ids for d,s,p in profiles]+[(0,4,0,0,1),(5,4,0,0,2)]
def run(q):
 c,d,s,p,f=q;label=f'c{c}_d{d}_s{s}_p{p}_f{f}';v=w/(label+'.vvp')
 a=subprocess.run(base+['-g2012','-I',str(r/'sim'),'-s','tb_madl_r13','-o',str(v)]+[f'-Ptb_madl_r13.{k}={v}' for k,v in dict(CASE=c,CPU_DIV=d,STRESS=s,PHASE=p,FAULT=f).items()]+[str(r/'sim/tb_madl_r13.sv'),str(r/'verification/cpu_1.v')],capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([vvp,str(v)],capture_output=True,text=True,timeout=1800);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 if f:assert a.returncode!=0 and ('frame write' if f==1 else 'MADL state') in out,out
 else:assert a.returncode==0 and 'PASS madl_r13' in out,out
 print('PASS MADL',q,flush=True);return dict(case=q,result=out[-900:])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
j=dict(fresh_runs=len(ids)*len(profiles),expected_failure_runs=2,cases=rows,logical_flat_RAM=True,not_board_mapping=True,STMIX_RSMIX_all_flags_and_ADL_Z80=True,IM1_IM2_NMI_from_both_modes=True,frame_wait_CEN_and_bus_request_checks=True,nested_NMI_and_pending_IRQ_at_RETN=True,RETI_L_RETN_L_LIS_LIL_layouts=True,unsupported_MADL_RST_guard=True,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')})
(r/'verification_madl_r13_result.json').write_text(json.dumps(j,indent=2)+'\n')
