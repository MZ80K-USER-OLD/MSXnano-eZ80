from pathlib import Path
from itertools import product
from parallel_matrix import run_matrix
root=Path(__file__).resolve().parent.parent
cases=[dict(zip(('OUTPUTTING','DECREMENTING','REPEATING','SHORT_MODE','ADDRESS_CASE','INITIAL_B','FLAG_SEED','INSERT_WAIT'),v)) for v in product((False,True),(False,True),(False,True),(False,True),range(3),(0,1,3),range(2),(False,True))]
if __name__=='__main__':
 print('PASS matrix '+str(run_matrix(root,'tb_block_io24',cases,'PASS block IO24')))
