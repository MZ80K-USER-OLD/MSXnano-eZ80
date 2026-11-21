"""R24.2 common load commit checks; --collect gathers completed fresh receipts."""
from pathlib import Path
import os,sys,subprocess,json,hashlib,shutil
r=Path(__file__).resolve().parent.parent;w=r/'verification_r24_2';w.mkdir(exist_ok=True);loc=r.parents[1];env=os.environ.copy()
for k,p in dict(GHDL='local-ghdl/usr/bin/ghdl',GHDL_PREFIX='local-ghdl/usr/lib/ghdl/mcode/vhdl',IVERILOG='local-iverilog/usr/bin/iverilog',IVL_ROOT='local-iverilog/usr/lib/x86_64-linux-gnu/ivl',VVP='local-iverilog/usr/bin/vvp').items():
 if (loc/p).exists():env.setdefault(k,str(loc/p))
for key,cmd in [('GHDL','ghdl'),('IVERILOG','iverilog'),('VVP','vvp')]:env.setdefault(key,shutil.which(cmd) or cmd)
checks=[
('verify_vhdl93_r11_1.py','verification_vhdl93_result.json','verification_vhdl93',{}),
('verify_load_decode_r24_2.py','verification_load_decode_r24_2/result.json','verification_load_decode_r24_2',{}),
('verify_load_matrix_r24_2.py','verification_load_matrix_r24_2/result.json','verification_load_matrix_r24_2',{}),
('verify_load_commit_r24_2.py','verification_load_commit_r24_2/result.json','verification_load_commit_r24_2',{}),
('verify_load_commit_r24_2.py','verification_load_commit_matrix_r24_2/result.json','verification_load_commit_matrix_r24_2',{'ATOMIC_MATRIX':'1'}),
('verify_mem_r4.py','verification_mem_r4_result.json','verification_mem_r4',{}),
('verify_mr4_r21_3.py','verification_mr4_r21_3/result.json','verification_mr4_r21_3',{}),
('verify_ldh_unit_r16.py','verification_ldh_unit_r16_result.json','verification_ldh_unit_r16_final',{}),
('verify_ldx_unit_r17.py','verification_ldx_unit_r17_result.json','verification_ldx_unit_r17_final',{}),
('verify_madl_r13.py','verification_madl_r13_result.json','verification_madl_r13',{'SMOKE':'1'}),
('verify_mixed_r14.py','verification_mixed_r14_result.json','verification_mixed_r14',{'SMOKE':'1'}),
('verify_prefix_com_r19_1.py','verification_prefix_com_r19_1_result.json','verification_prefix_com_r19_1',{'CASE_INDEX':'0,1'}),
('verify_im0_com_r19.py','verification_im0_com_r19_result.json','verification_im0_com_r19',{'CASE_INDEX':'0,1'}),
('verify_decode_com_r24.py','verification_decode_com_r24_result.json','verification_decode_com_r24',{'CASE_INDEX':'0,1'}),
('verify_decode_width_r24.py','verification_decode_width_r24/result.json','verification_decode_width_r24',{})]
if '--collect'not in sys.argv:
 subprocess.run([sys.executable,str(r/'tools/synthesize_r24_2.py')],cwd=r,env=env,check=True)
 for name,_,_,extra in checks:
  e=env.copy()
  for key in ['SMOKE','CASE_INDEX','CASES','ATOMIC_MATRIX','ATOMIC_TESTS']:e.pop(key,None)
  e.update(extra);print('Running',name,extra,flush=True);subprocess.run([sys.executable,str(r/'tools'/name)],cwd=r,env=e,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rtl={str(p.relative_to(r)):sha(p)for p in(r/'fpga/G80A_eZ80').glob('*.vhd')}
assert json.loads((r/'verification/r22_rtl_sha256.json').read_text())==rtl,'Model source mismatch'
rows=[]
for name,result,folder,extra in checks:
 d=json.loads((r/result).read_text());dest=w/'checks'/folder;dest.mkdir(parents=True,exist_ok=True)
 for key in ['sha256','rtl_sha256']:
  if key in d:
   for k,v in d[key].items():assert sha(r/k)==v,(name,k)
 if 'package_sha256'in d:assert sha(r/'fpga/G80A_eZ80/t80_pack_ez80.vhd')==d['package_sha256']
 shutil.copyfile(r/result,dest/'result.json');logs=sorted((r/folder).glob('*.log'));assert logs,name
 for p in logs:shutil.copyfile(p,dest/p.name)
 rows.append(dict(script=name,conditions=extra,result=d,log_sha256={p.name:sha(p)for p in logs}))
atomic=json.loads((r/'verification_load_commit_r24_2/result.json').read_text());matrix=json.loads((r/'verification_load_commit_matrix_r24_2/result.json').read_text())
assert atomic['family_coverage']==7 and matrix['family_coverage']==7 and atomic['expected_faults']==1
nominal=[q for q in atomic['cases']+matrix['cases']if not q['test'][2]]
assert all(q['captures']==q['commits']for q in nominal)
summary=dict(release='R24.2',basis='R24.1 interface; compared to hardware-confirmed R24',GOWIN=False,board=False,LUT_measured=False,GSR='deferred/unchanged',scope='Mode0 with extensions enabled: immediate/absolute/HL/IX-IY pair loads',atomic_commits=sum(q['commits']for q in nominal),WAIT_samples=sum(q['wait']for q in nominal),work_hold_checks=sum(q['held']for q in nominal),checks=rows,rtl_sha256=rtl,model_sha256={p.name:sha(p)for p in(r/'verification').glob('cpu_*.v')})
(w/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print('PASS R24.2 selected regressions:',summary['atomic_commits'],'atomic commits; GOWIN/board pending')
