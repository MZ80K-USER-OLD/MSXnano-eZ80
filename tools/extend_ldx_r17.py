"""Apply the R17 FPGA delta to an unmodified R16 source tree."""
from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent.parent
subprocess.run(['patch','--batch','--forward','-p1','-i',str(r/'doc/R17_LDX.patch')],cwd=r,check=True)
