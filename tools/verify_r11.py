from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for script in ('verify_r11_regression.py','convert_diag_r11.py','verify_irq_r11.py','verify_irq_unit_r11.py','verify_return_guard_r11.py','verify_no_diag_r11.py','verify_release_r11.py','summarize_r11.py'):
 subprocess.run([sys.executable,str(r/'tools'/script)],cwd=r,check=True)
