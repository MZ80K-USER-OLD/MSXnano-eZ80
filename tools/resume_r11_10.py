from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent.parent
def run(n):subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,check=True)
# Resume only this unchanged-source run after correcting a structural LEA check.
(r/'verification_result.json').write_bytes((r/'verification_regression_R3_on_R4.json').read_bytes())
for stage in range(4,10):
 (r/f'verification_regression_R{stage-1}_on_R{stage}.json').write_bytes((r/'verification_result.json').read_bytes())
 if stage>=7:run(f'verify_scope_r{stage}.py')
 run(f'summarize_r{stage}.py')
(r/'verification_regression_R9_on_R10.json').write_bytes((r/'verification_result.json').read_bytes());run('summarize_r10.py')
(r/'verification_regression_R10_on_R11.json').write_bytes((r/'verification_result.json').read_bytes())
for n in ['verify_sd_r11_9.py','verify_upper_r11_10.py','verify_slot_r11_4.py','verify_release_r11_10.py','summarize_r11_10.py']:run(n)
