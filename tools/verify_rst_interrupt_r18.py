from pathlib import Path
import os,json,hashlib,subprocess,concurrent.futures,shutil
r=Path(__file__).resolve().parent.parent;w=r/'verification_rst_interrupt_r18';w.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'sim/build_rst_r18.py')],check=True)
shutil.copyfile(r/'verification/cpu_1.v',w/'cpu_snapshot.v')
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
ids=list(range(104,112)) if not os.environ.get('CASES') else [int(x) for x in os.environ['CASES'].split(',')]
profiles=[(4,0,0)] if os.environ.get('SMOKE') else [(4,0,0),(4,1,3),(16,1,11)]
cases=[(c,d,s,p,0) for c in ids for d,s,p in profiles]
def run(q):
 c,d,s,p,f=q;label=f'c{c}_d{d}_s{s}_p{p}_f{f}';v=w/(label+'.vvp')
 a=subprocess.run(base+['-g2012','-I',str(r/'sim'),'-s','tb_rst_r18','-o',str(v)]+[f'-Ptb_rst_r18.{k}={v}' for k,v in dict(CASE=c,CPU_DIV=d,STRESS=s,PHASE=p,FAULT=f).items()]+[str(r/'sim/tb_rst_r18.sv'),str(w/'cpu_snapshot.v')],capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([vvp,str(v)],capture_output=True,text=True,timeout=1800);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 if f:assert a.returncode!=0 and 'frame write' in out,out
 else:assert a.returncode==0 and 'PASS rst_r18' in out,out
 print('PASS RST',q,flush=True);return dict(case=q,result=out[-900:])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
j=dict(fresh_runs=len(ids)*len(profiles),expected_failure_runs=0,cases=rows,logical_flat_RAM=True,not_board_mapping=True,canonical_suffix_cases=8,NMI_during_RST=True,IRQ_during_RET=True,IEF_preservation=True,all_8_vectors=False,vectors=[16],source_destination_modes=True,MADL_0_and_1=False,MADL=1,MBASE_0_and_14=False,MBASE=14,PC_stack_boundary=False,all_frame_writes_compared=True,WAIT_CEN_BUSRQ=True,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')})
(r/'verification_rst_interrupt_r18_result.json').write_text(json.dumps(j,indent=2)+'\n')
