from pathlib import Path
import subprocess,sys,concurrent.futures,json,hashlib
r=Path(__file__).resolve().parent.parent
def run(name):subprocess.run([sys.executable,str(r/'tools'/name)],cwd=r,check=True)
if '--reuse-write' in sys.argv:
 j=json.loads((r/'verification_write_r11_9_result.json').read_text())
 assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h for n,h in j['sha256'].items())
else:run('verify_write_r11_9.py')
if '--reuse-sd' in sys.argv:
 j=json.loads((r/'verification_sd_r11_9_result.json').read_text());assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h for n,h in j['sha256'].items())
run('verify_r3.py');run('convert_diag_r11.py')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for f in [pool.submit(run,n) for n in ['verify_parallel_r11_2.py','verify_cdc_r11_5.py','verify_exsp_work_r11_2.py','verify_msx_request_r11_3.py']]:f.result()
if '--reuse-sd' not in sys.argv:run('verify_sd_r11_9.py')
run('verify_slot_r11_4.py');run('verify_release_r11_9.py');run('summarize_r11_9.py')
