from pathlib import Path
from itertools import product
from contextlib import redirect_stdout
import io,os
from parallel_matrix import run_matrix
root=Path(__file__).resolve().parent.parent
cases=[dict(NATIVE_ADL=n,SUFFIX=3 if n else 0,TARGET=t,BOUNDARY=b,LOADING=l,INSERT_WAIT=w,EXPLICIT_SUFFIX=False) for n,t,b,l,w in product((False,True),range(7),range(3),(False,True),(False,True))]
if __name__=='__main__':
 stream=io.StringIO()
 with redirect_stdout(stream):count=run_matrix(root,'tb_suffix_absolute281',cases,'PASS absolute V2')
 s=stream.getvalue();assert s.count('simulation stopped')==count==168
 f=root/'test_results_native_absolute_v32.log';tmp=f.with_suffix('.tmp');tmp.write_text(s);os.replace(tmp,f)
 print('PASS native absolute',count,flush=True)
