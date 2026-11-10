"""Apply the R16 FPGA delta to an unmodified R15.3 source tree."""
from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent.parent
subprocess.run(['patch','--batch','--forward','-p1','-i',str(r/'doc/R16_LDH.patch')],cwd=r,check=True)
