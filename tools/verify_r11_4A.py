from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for n in ['verify_r3.py','verify_mem_r4.py','verify_platform_r11_1.py','verify_slot_r11_4.py','verify_release_r11_4.py','summarize_r11_4A.py']:
 subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,check=True)
