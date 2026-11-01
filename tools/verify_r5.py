from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for script in ('verify_r4.py','verify_alu_r5.py','verify_arith_corners_r5.py'):
 subprocess.run([sys.executable,str(r/'tools'/script)],cwd=r,check=True)
(r/'verification_regression_R4_on_R5.json').write_bytes((r/'verification_result.json').read_bytes())
subprocess.run([sys.executable,str(r/'tools/summarize_r5.py')],cwd=r,check=True)
