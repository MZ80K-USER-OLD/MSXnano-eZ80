from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for script in ('verify_r6.py','verify_mul_r7.py','verify_mul_corners_r7.py','verify_scope_r7.py'):
 subprocess.run([sys.executable,str(r/'tools'/script)],cwd=r,check=True)
(r/'verification_regression_R6_on_R7.json').write_bytes((r/'verification_result.json').read_bytes())
subprocess.run([sys.executable,str(r/'tools/summarize_r7.py')],cwd=r,check=True)
