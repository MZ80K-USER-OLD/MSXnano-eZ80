from pathlib import Path
import subprocess,sys,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent
def run(n):subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,check=True)
if '--reuse-write' in sys.argv:
 j=json.loads((r/'verification_write_r12_result.json').read_text());assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h for n,h in j['sha256'].items())
else:run('verify_write_r12.py')
if '--reuse-r3' in sys.argv:
 j=json.loads((r/'verification_result.json').read_text());assert j['series']=='restart R3';assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h for n,h in j['sha256'].items())
else:run('verify_r3.py')
run('convert_diag_r11.py')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for f in [pool.submit(run,n) for n in ['verify_parallel_r11_2.py','verify_cdc_r11_5.py','verify_exsp_work_r11_2.py','verify_msx_request_r11_3.py']]:f.result()
for n in ['verify_sd_r11_9.py','verify_upper_r12.py','verify_slot_r11_4.py','verify_mbase_r12.py','verify_release_r12.py','summarize_r12.py']:run(n)
