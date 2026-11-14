from pathlib import Path
import subprocess,sys,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent
def run(n):subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,check=True)
run('verify_write_r18.py')
run('verify_r3.py')
run('convert_diag_r11.py')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for f in [pool.submit(run,n) for n in ['verify_parallel_r11_2.py','verify_cdc_r11_5.py','verify_exsp_work_r11_2.py','verify_msx_request_r11_3.py']]:f.result()
run('verify_madl_r13.py')
for n in ['verify_sd_r11_9.py','verify_upper_r18.py','verify_slot_r11_4.py','verify_mbase_r12.py','verify_mixed_r14.py','verify_mix_nodiag_r14.py','verify_tst_r15.py','verify_tst_z80_r15.py','verify_tst_com_nodiag_r15.py','verify_diag_r15_1.py','verify_diag_r15_2.py','verify_ldh_unit_r16.py','verify_ldx_unit_r17.py','verify_ldx_com_nodiag_r17.py','verify_ldx_adl_irq_r17.py']:run(n)
