"""Re-run functional checks. Set GHDL, IVERILOG, IVL_ROOT and VVP for the installed tools.
The GOWIN/STA/physical-board checks are separate; this script does not run them.
"""
from pathlib import Path
import subprocess,sys,os
r=Path(__file__).resolve().parent.parent
for key in ('GHDL','IVERILOG','IVL_ROOT','VVP'):
    if not os.environ.get(key):raise SystemExit('Set '+key+' for the local tool installation')
# Keep model generation sequential, before consumers of the generated models.
for name in ('entry_r19','prefix_r19_1','prefix_com_r19_1','im0_r19','im0_edges_r19','im0_com_r19','rst_r18','mixed_r14','rst_interrupt_r18','irq_unit_r19','mem_r4','rw_diag_r18_3','board_r18_3','rst_com_r18','locked_r18_3','vhdl93_r11_1'):
    subprocess.run([sys.executable,str(r/'tools'/('verify_'+name+'.py'))],cwd=r,check=True)
print('PASS R19.1 functional release checks; GOWIN, physical timing and board not checked')
