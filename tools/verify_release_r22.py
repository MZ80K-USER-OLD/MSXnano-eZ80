"""Functional RTL/COM checks only. GOWIN timing/area and hardware are separate."""
from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for n in ['synthesize_r22','verify_ior_r22','verify_io2_r21','verify_ior_com_r22','verify_io2_com_r21','verify_mem_r4','verify_board_r18_3','verify_prefix_r19_1','verify_im0_r19','verify_vhdl93_r11_1','verify_mr4_r22_smoke']:
 subprocess.run([sys.executable,str(r/'tools'/(n+'.py'))],cwd=r,check=True)
print('PASS R22 functional checks; GOWIN/board/STA remain unverified')
