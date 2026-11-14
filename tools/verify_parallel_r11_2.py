from pathlib import Path
import concurrent.futures,subprocess,sys,time,json,os
r=Path(__file__).resolve().parent.parent;w=r/'verification_parallel';w.mkdir(exist_ok=True)
jobs=['verify_mem_r4.py','verify_corners_r4.py','verify_alu_r5.py','verify_arith_corners_r5.py','verify_blk_r6.py','verify_block_corners_r6.py','verify_mul_r7.py','verify_mul_corners_r7.py','verify_lea_r8.py','verify_lea_corners_r8.py','verify_fetch_r9.py','verify_pc_r9.py','verify_adl_r10.py','verify_control_r10.py','verify_flow_r10.py','verify_mixed_guard_r10.py','verify_irq_r11.py','verify_irq_unit_r11.py','verify_return_guard_r11.py','verify_no_diag_r11.py','verify_legacy_branches_r11_1.py','verify_platform_r11_1.py','verify_vhdl93_r11_1.py']
def run(n):
 with (w/(n+'.log')).open('w') as log:p=subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,stdout=log,stderr=subprocess.STDOUT)
 print(('PASS ' if p.returncode==0 else 'FAIL ')+n,flush=True);return n,p.returncode
with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get('CHECK_JOBS','6'))) as pool:results=list(pool.map(run,jobs))
assert all(code==0 for _,code in results),results
# R3 runs before this command in the standard entry point; no top-level result
# file is mutated by the independent leaf suites above.
assert json.loads((r/'verification_result.json').read_text())['series']=='restart R3'
for stage in range(4,10):
 prior={4:3,5:4,6:5,7:6,8:7,9:8}[stage]
 (r/f'verification_regression_R{prior}_on_R{stage}.json').write_bytes((r/'verification_result.json').read_bytes())
 if stage>=7:subprocess.run([sys.executable,str(r/'tools'/f'verify_scope_r{stage}.py')],cwd=r,check=True)
 subprocess.run([sys.executable,str(r/'tools'/f'summarize_r{stage}.py')],cwd=r,check=True)
(r/'verification_regression_R9_on_R10.json').write_bytes((r/'verification_result.json').read_bytes())
subprocess.run([sys.executable,str(r/'tools/summarize_r10.py')],cwd=r,check=True)
(r/'verification_regression_R10_on_R11.json').write_bytes((r/'verification_result.json').read_bytes())
print('PASS complete CPU regression leaf suites and ordered aggregation',flush=True)
