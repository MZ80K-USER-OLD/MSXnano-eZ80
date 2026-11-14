from pathlib import Path
from itertools import product
from parallel_matrix import run_matrix
root=Path(__file__).resolve().parent.parent
cases=[dict(zip(('NATIVE_ADL','SUFFIX','TARGET','VALUE_CASE','CHAINED','INSERT_WAIT'),v)) for v in product((False,True),range(4),range(6),range(3),(False,True),(False,True))]
if __name__=='__main__':print('PASS suffix matrix '+str(run_matrix(root,'tb_suffix_width28',cases,'PASS suffix')))
