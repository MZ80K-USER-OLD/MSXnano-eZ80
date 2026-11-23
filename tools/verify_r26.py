"""Reproduce R26 functional checks. Requires GHDL 5+, Icarus and Python 3."""
from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1]
for name in ['synthesize_r26.py','verify_window_request_r26.py','verify_window_com_r26.py','verify_window_irq_r26.py','verify_tstio_com_r26.py','verify_mem_r4.py','verify_mr4_r21_3.py','verify_regression_r25.py','verify_compat_coms_r26.py','verify_release_r26.py']:
 print('Running',name,flush=True)
 subprocess.run([sys.executable,str(r/'tools'/name)],cwd=r,check=True)
