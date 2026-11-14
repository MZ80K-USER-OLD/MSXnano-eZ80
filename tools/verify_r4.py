from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for script in ('verify_r3.py','verify_mem_r4.py','verify_corners_r4.py'):
 subprocess.run([sys.executable,str(r/'tools'/script)],cwd=r,check=True)
# The R3 regression runner uses its historical result filename; preserve it per run.
(r/'verification_regression_R3_on_R4.json').write_bytes((r/'verification_result.json').read_bytes())
subprocess.run([sys.executable,str(r/'tools/summarize_r4.py')],cwd=r,check=True)
