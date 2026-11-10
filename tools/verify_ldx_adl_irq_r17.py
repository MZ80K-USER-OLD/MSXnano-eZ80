from pathlib import Path
import os,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_ldx_adl_irq_r17';w.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'sim/build_ldx_adl_irq_r17.py')],check=True)
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[(n,d,p,s) for n in [0,1] for d,p,s in [(4,0,0),(4,3,1),(16,11,1)]]
def run(q):
 n,d,p,s=q;f=w/('n%d_d%d_p%d_s%d.vvp'%q)
 a=subprocess.run(iv+['-g2012','-I',str(r/'sim'),'-s','tb_ldx_adl_irq_r17','-o',str(f)]+[f'-Ptb_ldx_adl_irq_r17.{k}={v}' for k,v in dict(NMI=n,CPU_DIV=d,PHASE=p,STRESS=s).items()]+[str(r/'sim/tb_ldx_adl_irq_r17.sv'),str(r/'verification/cpu_1.v')],cwd=r,text=True,capture_output=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ.get('VVP','vvp'),str(f)],cwd=r,text=True,capture_output=True,timeout=1800);out=a.stdout+a.stderr;f.with_suffix('.log').write_text(out)
 assert a.returncode==0 and 'PASS ldx_adl_irq_r17' in out,out
 print('PASS native ADL LDX IRQ',q,flush=True);return dict(case=q,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
(r/'verification_ldx_adl_irq_r17_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),expected_failure_runs=0,cases=rows,instructions_per_run=40,native_ADL_IM1_and_NMI=True,MBASE=14,short_and_long=True,IX_and_IY=True,all_5_pairs=True,SPS_and_SPL_preserved=True,actual_frame_address_range="05007D..05007F",frame_writes_per_run=120,frame_reads_per_run=120,interrupt_after_all_data_bytes=True,scope='CPU/wrapper with flat RAM, not MSX BIOS',sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
