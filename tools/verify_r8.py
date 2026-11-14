from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for script in ('verify_r7.py','verify_lea_r8.py','verify_lea_corners_r8.py','verify_scope_r8.py'):
 subprocess.run([sys.executable,str(r/'tools'/script)],cwd=r,check=True)
(r/'verification_regression_R7_on_R8.json').write_bytes((r/'verification_result.json').read_bytes())
subprocess.run([sys.executable,str(r/'tools/summarize_r8.py')],cwd=r,check=True)
