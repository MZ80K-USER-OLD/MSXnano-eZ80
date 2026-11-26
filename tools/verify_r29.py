"""R29 functional regression. GHDL 5+, Icarus and Python 3 required."""
from pathlib import Path
import subprocess,sys,os
r=Path(__file__).resolve().parents[1]
os.environ['NAMES']='EZ80MEM,EZ80WIN,EZ80CTL,EZ80TIO,EZ80IRQ,EZ80IM2,EZ80NMI,EZ80MIX,EZ80MAD'
for n in ['synthesize_r29.py','verify_input_frame_r29.py','verify_strobes_r28.py','verify_vdp_io_r28.py','verify_window_com_r26.py','verify_window_irq_r26.py','verify_tstio_com_r26.py','verify_mem_r4.py','verify_mr4_r21_3.py','verify_regression_r25.py','verify_compat_coms_r26.py','verify_differential_r27.py']:
 env1=os.environ.copy()
 if n!='verify_differential_r27.py':env1.pop('NAMES',None)
 subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,env=env1,check=True)
env=os.environ.copy();env.update(STRESS='1',NAMES='EZ80WIN,EZ80CTL,EZ80IRQ,EZ80IM2,EZ80NMI,EZ80MIX,EZ80MAD')
subprocess.run([sys.executable,str(r/'tools/verify_differential_r27.py')],cwd=r,env=env,check=True)
subprocess.run([sys.executable,str(r/'tools/verify_release_r29.py')],cwd=r,check=True)
