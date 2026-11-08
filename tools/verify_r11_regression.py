from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
def run(n):subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,check=True)
for n in ('verify_r9.py','verify_adl_r10.py','verify_control_r10.py','verify_flow_r10.py','verify_mixed_guard_r10.py'):
 run(n)
 if n=='verify_r9.py':(r/'verification_regression_R9_on_R10.json').write_bytes((r/'verification_result.json').read_bytes())
run('summarize_r10.py')
(r/'verification_regression_R10_on_R11.json').write_bytes((r/'verification_result.json').read_bytes())
