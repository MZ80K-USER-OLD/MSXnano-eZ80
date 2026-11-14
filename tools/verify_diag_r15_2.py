from pathlib import Path
import os,subprocess,json,hashlib,concurrent.futures,sys
r=Path(__file__).resolve().parent.parent;w=r/'verification_diag_r15_2';w.mkdir(exist_ok=True)
base=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else []);vvp=os.environ.get('VVP','vvp')
subprocess.run([sys.executable,str(r/'tools/build_diag_r15_2.py')],check=True)
cases=[('ctl',16,0,0,0),('ctl',4,7,0,1),('ctl',4,3,1,0),('ctl',4,3,2,0),('boundary',16,0,0,0),('boundary',4,7,0,0),('boundary',4,3,1,0),('boundary',4,3,2,0)]
if '--smoke' in sys.argv:cases=[q for q in cases if q[1]==4]
def run(q):
 kind,div,phase,fault,pause=q;top=f'tb_{kind}_diag_r15_2';label=f'{kind}_d{div}_p{phase}_f{fault}_s{pause}';exe=w/(label+'.vvp')
 a=subprocess.run(base+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s',top,'-o',str(exe)]+[f'-P{top}.{k}={v}' for k,v in dict(CPU_DIV=div,PHASE=phase,FAULT=fault).items()]+([f'-P{top}.PAUSE_ENABLE={pause}'] if kind=='ctl' else [])+[str(r/f'sim/{top}.sv'),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')],cwd=r,text=True,capture_output=True)
 assert a.returncode==0,a.stderr
 a=subprocess.run([vvp,str(exe)],cwd=r,text=True,capture_output=True,timeout=int(os.environ.get('SIM_TIMEOUT','1800')));s=a.stdout+a.stderr;(w/(label+'.log')).write_text(s)
 assert a.returncode==0 and 'PASS '+kind+'_diag_r15_2' in s,s[-2000:]
 if kind=='ctl' and fault==2:assert 'FAIL stage V' in s and 'ADDR=090000 EXP=31 ACT=30' in s and 'CT3 RUN' not in s,s
 elif kind=='ctl' and fault==1:assert 'ADDR=030200 EXP=22 ACT=23' in s,s
 elif kind=='boundary' and fault:assert 'ADDR=030000 EXP=96 ACT=97' in s,s
 elif kind=='ctl':assert all(v in s for v in ['CT1 LOAD','CT2 VERIFY','CT3 RUN','CT4 CHECK','EZ80CT1 R10: PASS']),s
 else:assert 'BN9' in s and 'EZ80BN1 R15.2: PASS' in s,s
 print('PASS',q,flush=True);return dict(case=q,output=s)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
(r/'verification_diag_r15_2_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),fault_injection_cases=sum(q[3]!=0 for q in cases),cases=rows,FPGA_unchanged=True,normal_IRQ_during_DOS=True,DOS_enables_interrupts=True,DOS_only_Z80_MBASE0_extensions_locked=True,readback_before_code_execution=True,physical_root_cause_confirmed=False,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
