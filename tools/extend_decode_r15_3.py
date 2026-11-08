from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent.parent
subprocess.run(['patch','--batch','--forward','-p1','-i',str(r/'doc/R15_3_TST_DECODE.patch')],cwd=r,check=True)
