"""ADC/SBC signed and unsigned arithmetic cases, in isolated GHDL libraries."""
import itertools
from pathlib import Path
from parallel_matrix import run_matrix
cases=[dict(SUBTRACTING=u,SOURCE=s,VECTOR=v,CARRY_IN=c,SHORT_MODE=n,INSERT_WAIT=w) for u,s,v,c,n,w in itertools.product((False,True),range(4),range(16),(False,True),(False,True),(False,True))]
count=run_matrix(Path(__file__).resolve().parent.parent,'tb_adc_sbc24',cases,'PASS ADC/SBC24')
print(f'PASS all {count} ADC/SBC24 cases',flush=True)
