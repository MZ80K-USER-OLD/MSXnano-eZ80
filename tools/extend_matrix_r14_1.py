from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent.parent
subprocess.run(['patch','--batch','--forward','-p1','-i',str(r/'doc/R14_1_MATRIX.patch')],cwd=r,check=True)
