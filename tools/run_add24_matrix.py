"""ADD24 and short ADD, in isolated GHDL libraries with explicit completion checks."""
import itertools
from pathlib import Path
from parallel_matrix import run_matrix
cases=[dict(DESTINATION=d,SOURCE=s,VECTOR=v,SHORT_MODE=n,INSERT_WAIT=w) for d,s,v,n,w in itertools.product(range(3),range(4),range(8),(False,True),(False,True))]
count=run_matrix(Path(__file__).resolve().parent.parent,'tb_add24',cases,'PASS ADD24')
print(f'PASS all {count} ADD24 cases',flush=True)
