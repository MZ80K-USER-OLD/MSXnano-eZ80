from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
def run(script):subprocess.run([sys.executable,str(r/script)],cwd=r,check=True)
run('hardware_test/build_control_r10.py')
for script in ('verify_r9.py','verify_adl_r10.py','verify_control_r10.py','verify_flow_r10.py','verify_mixed_guard_r10.py','verify_release_r10.py'):
 run('tools/'+script)
 if script=='verify_r9.py':(r/'verification_regression_R9_on_R10.json').write_bytes((r/'verification_result.json').read_bytes())
run('tools/summarize_r10.py')
