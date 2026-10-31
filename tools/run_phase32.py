from pathlib import Path
from itertools import product
from contextlib import redirect_stdout
import io,os
from parallel_matrix import run_matrix
root=Path(__file__).resolve().parent.parent
cases={name:[] for name in ['tb_decimal32','tb_restart32','tb_relative32']}
for n,w,b,a,v,l,c,wait in product((False,True),range(5),(0,126),range(3),range(4),(False,True),(False,True),(False,True)):
 cases['tb_decimal32'].append(dict(NATIVE_ADL=n,WIDTH=w,BASE=b,ADDRESS_CASE=a,VALUE=v,LEFTWARD=l,CARRY_IN=c,INSERT_WAIT=wait))
assert len(cases['tb_decimal32'])==1920
for low,l,c in product(range(16),(False,True),(False,True)):
 cases['tb_decimal32'].append(dict(BATCH=True,LOW=low,LEFTWARD=l,CARRY_IN=c))
for n,v,b,base,wait in product((False,True),range(8),range(3),(0,126),(False,True)):
 cases['tb_restart32'].append(dict(NATIVE_ADL=n,VECTOR=v,BOUNDARY=b,BASE=base,INSERT_WAIT=wait))
for n,kind,d,p,b,wait in product((False,True),range(6),(-128,-1,0,127),range(4),(0,126),(False,True)):
 for taken in ((True,) if kind in (0,5) else (False,True)):
  for counter in ((0,1,2,255) if kind==5 else (2,)):
   cases['tb_relative32'].append(dict(NATIVE_ADL=n,KIND=kind,DISPLACEMENT=d,POSITION=p,BASE=b,INSERT_WAIT=wait,TAKEN=taken,INITIAL_B=counter))
assert len(cases['tb_restart32'])==192 and len(cases['tb_relative32'])==1664
assert sum(map(len,cases.values()))==3840
if __name__=='__main__':
 stream=io.StringIO();total=0
 with redirect_stdout(stream):
  for name,group in cases.items():total+=run_matrix(root,name,group,'PASS v32',workers=8,work_name='verification_phase32')
 s=stream.getvalue();assert s.count('simulation stopped')==total
 f=root/'test_results_phase_focus_v32.log';tmp=f.with_suffix('.tmp');tmp.write_text(s);os.replace(tmp,f)
 print('PASS v32 focused executions',total,flush=True)
