from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
for script in ('verify_r5.py','verify_blk_r6.py','verify_block_corners_r6.py'):
 subprocess.run([sys.executable,str(r/'tools'/script)],cwd=r,check=True)
(r/'verification_regression_R5_on_R6.json').write_bytes((r/'verification_result.json').read_bytes())
subprocess.run([sys.executable,str(r/'tools/summarize_r6.py')],cwd=r,check=True)
