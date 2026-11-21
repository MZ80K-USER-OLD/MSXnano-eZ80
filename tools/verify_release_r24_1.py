"""R24.1 comparison checks. --collect retains completed run receipts."""
from pathlib import Path
import os,sys,subprocess,json,hashlib,shutil
r=Path(__file__).resolve().parent.parent;w=r/'verification_r24_1';w.mkdir(exist_ok=True);loc=r.parents[1];env=os.environ.copy()
for k,p in dict(GHDL='local-ghdl/usr/bin/ghdl',GHDL_PREFIX='local-ghdl/usr/lib/ghdl/mcode/vhdl',IVERILOG='local-iverilog/usr/bin/iverilog',IVL_ROOT='local-iverilog/usr/lib/x86_64-linux-gnu/ivl',VVP='local-iverilog/usr/bin/vvp').items():
 if (loc/p).exists():env.setdefault(k,str(loc/p))
checks=[('verify_vhdl93_r11_1.py','verification_vhdl93_result.json','verification_vhdl93',{}),('verify_reg24_differential.py','verification_reg24_diff/result.json','verification_reg24_diff',{}),('trace_reg24_addresses.py','verification_reg24_trace/result.json','verification_reg24_trace',{}),('verify_mem_r4.py','verification_mem_r4_result.json','verification_mem_r4',{}),('verify_ldh_unit_r16.py','verification_ldh_unit_r16_result.json','verification_ldh_unit_r16_final',{}),('verify_ldx_unit_r17.py','verification_ldx_unit_r17_result.json','verification_ldx_unit_r17_final',{}),('verify_madl_r13.py','verification_madl_r13_result.json','verification_madl_r13',{'SMOKE':'1'}),('verify_mixed_r14.py','verification_mixed_r14_result.json','verification_mixed_r14',{'SMOKE':'1'}),('verify_decode_com_r24.py','verification_decode_com_r24_result.json','verification_decode_com_r24',{'CASE_INDEX':'0,1'})]
if '--collect' not in sys.argv:
 subprocess.run([sys.executable,str(r/'tools/synthesize_r22.py')],cwd=r,env=env,check=True)
 for name,_,_,extra in checks:
  e=env.copy()
  for key in ['SMOKE','CASE_INDEX','CASES']:e.pop(key,None)
  e.update(extra);print('Running',name,flush=True);subprocess.run([sys.executable,str(r/'tools'/name)],cwd=r,env=e,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rtl={str(p.relative_to(r)):sha(p)for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}
assert json.loads((r/'verification/r22_rtl_sha256.json').read_text())==rtl
rows=[]
for name,result,folder,extra in checks:
 d=json.loads((r/result).read_text());dest=w/'checks'/name.removesuffix('.py');dest.mkdir(parents=True,exist_ok=True)
 if 'sha256'in d:
  for k,v in d['sha256'].items():assert sha(r/k)==v,(name,k)
 if name=='verify_reg24_differential.py':
  assert d['event_coverage_mask']==255 and any(q['exchanges']for q in d['tests'])
 shutil.copyfile(r/result,dest/'result.json');logs=sorted((r/folder).glob('*.log'));assert logs,name
 for p in logs:shutil.copyfile(p,dest/p.name)
 rows.append(dict(test=name,conditions=extra,result=d,logs={p.name:sha(p)for p in logs}))
(w/'summary.json').write_text(json.dumps(dict(release='R24.1 register interface comparison',GOWIN=False,board=False,LUT_reduction_measured=False,baseline='hardware-confirmed R24 Logic97%',GSR='deferred and unchanged',rtl_sha256=rtl,checks=rows),ensure_ascii=False,indent=2)+'\n')
print('PASS R24.1 selected regressions. GOWIN area/timing and board checks pending.')
