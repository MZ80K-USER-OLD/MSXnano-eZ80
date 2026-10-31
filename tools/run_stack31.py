from pathlib import Path
from itertools import product
from contextlib import redirect_stdout
import io,os
from parallel_matrix import run_matrix
root=Path(__file__).resolve().parent.parent
cases=[]
for native,kind,width,boundary,value,base,wait in product((False,True),range(3),range(5),range(4),range(4),(0,126),(False,True)):
 for target in (range(3) if kind==2 else (0,)):
  for chain in ((False,True) if width and boundary==0 and value==0 else (False,)):
   cases.append(dict(NATIVE_ADL=native,KIND=kind,TARGET=target,WIDTH=width,BOUNDARY=boundary,VALUE=value,FLAG_SEED=(0,255,165,90)[value],BASE=base,ALT_BANK=(kind==2 and value==3),CHAIN=chain,INSERT_WAIT=wait))
assert len(cases)==3360
# Exhaustively restore all 8 flag bits through native POP AF, both modes and WAIT.
for native,flag,wait in product((False,True),range(1,256),(False,True)):
 cases.append(dict(NATIVE_ADL=native,KIND=1,TARGET=0,WIDTH=0,BOUNDARY=1,VALUE=0,FLAG_SEED=flag,BASE=0,ALT_BANK=False,CHAIN=False,INSERT_WAIT=wait))
assert len(cases)==4380
if __name__=='__main__':
 stream=io.StringIO()
 with redirect_stdout(stream):count=run_matrix(root,'tb_stack31',cases,'PASS v31',workers=8,work_name='verification_stack31')
 s=stream.getvalue();assert s.count('simulation stopped')==count
 f=root/'test_results_stack_focus_v31.log';tmp=f.with_suffix('.tmp');tmp.write_text(s);os.replace(tmp,f)
 print('PASS v31 AF/EX SP focused cases',count,flush=True)
