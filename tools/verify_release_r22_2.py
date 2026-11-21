"""Compare the isolated ED decoder, then run functional checks. No GOWIN/board run."""
from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for n in ['verify_decode_scope_r22_2','verify_mcode_r22_2','synthesize_r22','verify_ior_r22','verify_io2_r21','verify_mem_r4','verify_vhdl93_r11_1','verify_board_r18_3','verify_mr4_r22_smoke','verify_ior_com_r22','verify_ior_diag_r22_1']:
 subprocess.run([sys.executable,str(r/'tools'/(n+'.py'))],cwd=r,check=True)
print('PASS R22.2 functional checks; GOWIN/area/STA/board remain unverified')
