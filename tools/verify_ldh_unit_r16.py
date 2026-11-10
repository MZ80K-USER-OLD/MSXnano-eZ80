from pathlib import Path
import os,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_ldh_unit_r16_final';w.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'sim/build_ldh_unit_r16.py')],check=True)
subprocess.run(['python3',str(r/'sim/build_ldh_unit_r16.py'),'--irq'],check=True)
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[(4,0,0,0,0),(4,3,1,0,0),(16,7,1,0,0),(4,1,1,1,0),(4,3,1,0,1),(4,1,1,0,2)]
def run(q):
 div,phase,pause,fault,irq=q;p=w/('d%d_p%d_s%d_f%d_i%d.vvp'%q)
 a=subprocess.run(iv+['-g2012',f'-DTEST_HEADER="test{"_irq" if irq else ""}.vh"','-I',str(r/'sim/ldh_r16'),'-s','tb_ldh_unit_r16','-o',str(p)]+[f'-Ptb_ldh_unit_r16.{k}={v}' for k,v in dict(CPU_DIV=div,PHASE=phase,PAUSE=pause,FAULT=fault,IRQ_STRESS=irq).items()]+[str(r/'sim/tb_ldh_unit_r16.sv'),str(r/'verification/cpu_1.v')],cwd=r,text=True,capture_output=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ.get('VVP','vvp'),str(p)],cwd=r,text=True,capture_output=True,timeout=1800);s=a.stdout+a.stderr;p.with_suffix('.log').write_text(s)
 assert a.returncode==0 and 'PASS ldh_unit_r16' in s,s
 print('PASS LDH unit',q,flush=True);return dict(case=q,output=s)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
(r/'verification_ldh_unit_r16_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),fault_injection_runs=1,cases=rows,instructions_per_normal_run=40,IM1_after_EI_delayed_across_complete_indirect_instruction=True,NMI_mid_transfer_delivered_after_instruction=True,all_four_width_prefixes=True,short_wrap_FFFF_to_0000=True,long_carry_03FFFF_to_040000=True,flags_preserved=True,overlapping_HL_address_preserved=True,work_address_and_data_shared_with_EX_SP=True,scope='CPU and wrapper with byte RAM model; physical secondary-slot RTL is checked in separate integration suites',sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
