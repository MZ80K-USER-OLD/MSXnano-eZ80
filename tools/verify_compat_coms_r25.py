from pathlib import Path
import subprocess,os,json,concurrent.futures
r=Path(__file__).resolve().parents[1];w=r/'verification_compat_coms_r25';w.mkdir(exist_ok=True)
tests=['verify_decode_com_r24.py','verify_prefix_com_r19_1.py','verify_im0_com_r19.py','verify_tst_com_nodiag_r15.py','verify_io_nop_com_r23_2.py']
def run(name):
 env=os.environ.copy();env['SMOKE']='1'
 p=subprocess.run(['python3',str(r/'tools'/name)],cwd=r,env=env,capture_output=True,text=True,timeout=900)
 (w/(name+'.log')).write_text(p.stdout+p.stderr);assert not p.returncode,p.stdout[-3000:]+p.stderr[-3000:]
 print('PASS old COM',name,flush=True);return name
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,tests))
(w/'result.json').write_text(json.dumps({'passed_scripts':rows,'SMOKE':True,'GOWIN':False,'board':False},indent=2)+'\n')
