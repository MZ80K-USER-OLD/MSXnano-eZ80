"""R27 functional regression. GHDL 5+, Icarus and Python 3 required."""
from pathlib import Path
import subprocess,sys,os
r=Path(__file__).resolve().parents[1]
for n in ['synthesize_r27.py','verify_prepared_request_r27.py','verify_window_com_r26.py','verify_window_irq_r26.py','verify_tstio_com_r26.py','verify_mem_r4.py','verify_mr4_r21_3.py','verify_regression_r25.py','verify_compat_coms_r26.py','verify_differential_r27.py']:
 subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,check=True)
env=os.environ.copy();env.update(STRESS='1',NAMES='EZ80WIN,EZ80TIO,EZ80CTL,EZ80BLK')
subprocess.run([sys.executable,str(r/'tools/verify_differential_r27.py')],cwd=r,env=env,check=True)
subprocess.run([sys.executable,str(r/'tools/verify_release_r27.py')],cwd=r,check=True)
