from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for n in ['verify_r11_regression.py','convert_timing_r11_1.py','verify_irq_r11.py','verify_irq_unit_r11.py','verify_return_guard_r11.py','verify_no_diag_r11.py','verify_legacy_branches_r11_1.py','verify_platform_r11_1.py','verify_vhdl93_r11_1.py','verify_release_r11_1.py','summarize_r11_1.py']:
 subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,check=True)
