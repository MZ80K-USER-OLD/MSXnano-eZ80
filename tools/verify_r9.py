from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
subprocess.run([sys.executable,str(r/'hardware_test/build_fetch_r9.py')],cwd=r,check=True)
for script in ('verify_r8.py','verify_fetch_r9.py','verify_pc_r9.py','verify_scope_r9.py'):
 subprocess.run([sys.executable,str(r/'tools'/script)],cwd=r,check=True)
(r/'verification_regression_R8_on_R9.json').write_bytes((r/'verification_result.json').read_bytes())
subprocess.run([sys.executable,str(r/'tools/summarize_r9.py')],cwd=r,check=True)
