from pathlib import Path
import os,subprocess,json,concurrent.futures,hashlib
r=Path(__file__).resolve().parents[1];w=r/'verification_recovery_r29_1';w.mkdir(exist_ok=True)
specs=[(n,False)for n in ['EZ80MX0','EZ80MX1','EZ80MX2','EZ80MA1','EZ80MIX','EZ80MAD']]+[(n,True)for n in ['EZ80MX0','EZ80MX1','EZ80MX2','EZ80MA1']]
def run(q):
 n,stress=q;tag=n+('_stress'if stress else'');m=json.loads((r/'hardware_test'/(n+'.json')).read_text());p=r/'hardware_test'/(n+'.COM');hdr=w/(n+'.vh')
 hdr.write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in m['labels'].items())+f"`define P2_COM_END 16'h{255+p.stat().st_size:04x}\n")
 c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-I',str(w),f'-DTEST_HEADER="{n}.vh"',f'-DTEST_HEX="hardware_test/{n}.hex"','-s','tb_compat_com_r26','-o',str(w/(tag+'.vvp')),'-Ptb_compat_com_r26.CPU_DIV=4']
 if stress:c+=['-Ptb_compat_com_r26.PHASE=3','-Ptb_compat_com_r26.PAUSE_ENABLE=1']
 c+=[str(r/'sim/tb_compat_com_r26.sv'),str(r/'verification/cpu_diag.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 a=subprocess.run(c,cwd=r,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([os.environ['VVP'],str(w/(tag+'.vvp'))],cwd=r,capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;(w/(tag+'.log')).write_text(out)
 assert not a.returncode and 'PASS compat_com_r26'in out,(tag,out[-1000:])
 if n in ['EZ80MX0','EZ80MX1','EZ80MX2','EZ80MA1']:assert n+' R29.1: START'in out and n+' R29.1: PASS'in out,out[-1000:]
 print('PASS',tag,flush=True);return dict(COM=n,stress=stress,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),log=tag+'.log',passed=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(run,specs))
(w/'result.json').write_text(json.dumps(dict(tests=rows,CPU_divider=4,actual_CPU_SDRAM=True,BDOS_EI=True,board=False),indent=2)+'\n')
