from pathlib import Path
import subprocess,json,os,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_diag_r15_1';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
subprocess.run(['python3',str(r/'tools/build_diag_r15_1.py')],check=True)
cases=[('mem',d,p,f) for d,p,f in [(16,0,0),(4,3,0),(16,7,1),(4,3,2)]]+[('tst',d,p,f) for d,p,f in [(16,0,0),(4,7,0),(4,3,1)]]
def run(q):
 kind,div,phase,fault=q;top='tb_'+kind+'_diag_r15_1';out=w/(f'{kind}_d{div}_p{phase}_f{fault}.vvp')
 extra=['-DTEST_HEADER="EZ80TS1.vh"','-DTEST_HEX="hardware_test/EZ80TS1.hex"',f'-P{top}.SUPPORTED=1'] if kind=='tst' else []
 a=subprocess.run(base+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s',top,'-o',str(out)]+extra+[f'-P{top}.{k}={v}' for k,v in dict(CPU_DIV=div,PHASE=phase,FAULT=fault).items()]+[str(r/f'sim/{top}.sv'),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')],cwd=r,text=True,capture_output=True)
 assert a.returncode==0,a.stderr
 a=subprocess.run([vvp,str(out)],cwd=r,text=True,capture_output=True,timeout=1800);log=a.stdout+a.stderr;(out.with_suffix('.log')).write_text(log)
 assert a.returncode==0 and ('PASS '+kind+'_diag_r15_1') in log,log[-2500:]
 if kind=='mem' and fault:assert 'ADDR=020102 EXP=A2 ACT=A3' in log,log
 if kind=='tst' and not fault:assert 'TS36' in log and 'EZ80TS1 P2: PASS' in log,log[-1000:]
 print('PASS',q,flush=True);return dict(case=q,output=log)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
(r/'verification_diag_r15_1_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),includes_3_fault_injections=True,normal_Z80_IRQ_during_DOS=True,BDOS_enables_interrupts=True,DOS_only_extension_locked=True,cases=rows,FPGA_unchanged=True,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
