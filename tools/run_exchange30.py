from pathlib import Path
from itertools import product
from contextlib import redirect_stdout
import io,os,json
from parallel_matrix import run_matrix
root=Path(__file__).resolve().parent.parent
cases=[]
for native,kind,alt,value,base,wait in product((False,True),range(3),(False,True),range(4),(0,126),(False,True)):
 for target in (range(3) if kind==2 else (0,)):
  for width in ((0,) if kind==1 else range(5)):
   for chain in ((False,True) if width else (False,)):
    cases.append(dict(NATIVE_ADL=native,KIND=kind,TARGET=target,WIDTH=width,ALT_BANK=alt,VALUE=value,BASE=base,CHAIN=chain,INSERT_WAIT=wait))
assert len(cases)==2368
if __name__=='__main__':
 stream=io.StringIO()
 with redirect_stdout(stream):count=run_matrix(root,'tb_exchange_sp30',cases,'PASS v30',workers=8,work_name='verification_exchange30')
 s=stream.getvalue();assert s.count('simulation stopped')==count
 f=root/'test_results_exchange_focus_v30.log';tmp=f.with_suffix('.tmp');tmp.write_text(s);os.replace(tmp,f)
 print('PASS v30 focused exchange/SP',count,flush=True)
