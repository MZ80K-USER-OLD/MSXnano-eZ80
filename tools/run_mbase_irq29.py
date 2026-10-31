from pathlib import Path
from itertools import product
from contextlib import redirect_stdout
import io,os
from parallel_matrix import run_matrix
root=Path(__file__).resolve().parent.parent
cases=[dict(BASE=b,KIND=k,INSERT_WAIT=w) for b,k,w in product((0,1,126,255),range(4),(False,True))]
if __name__=='__main__':
 stream=io.StringIO()
 with redirect_stdout(stream):count=run_matrix(root,'tb_mbase_irq29',cases,'PASS MBASE Z80-mode',work_name='verification_irq29')
 s=stream.getvalue();assert s.count('simulation stopped')==count==32
 f=root/'test_results_mbase_irq_v29.log';tmp=f.with_suffix('.tmp');tmp.write_text(s);os.replace(tmp,f)
 print('PASS MBASE Z80-mode interrupt cases',count,flush=True)
