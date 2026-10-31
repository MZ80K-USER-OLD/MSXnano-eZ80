"""Check CPI/CPD/CPIR/CPDR with independently calculated results and explicit completion."""
import itertools
import subprocess
from pathlib import Path
cwd=Path(__file__).resolve().parent.parent/'verification'
cases=[]
for repeat,down,short,addr,carry,wait in itertools.product((False,True),(False,True),(False,True),range(3),(False,True),(False,True)):
 for scenario in range(4 if repeat else 5):
  case=dict(REPEATING=repeat,DECREMENTING=down,SHORT_MODE=short,ADDRESS_CASE=addr,CARRY_IN=carry,INSERT_WAIT=wait)
  case['STOP_CASE' if repeat else 'VALUE_CASE']=scenario
  cases.append(case)
for down,addr,carry,wait in itertools.product((False,True),range(3),(False,True),(False,True)):
 cases.append(dict(REPEATING=True,HIGH_REPEAT=True,DECREMENTING=down,ADDRESS_CASE=addr,CARRY_IN=carry,INSERT_WAIT=wait))
for case in cases:
 subprocess.run(['ghdl','-a','--std=08','-fsynopsys','../sim/tb_block_compare24.vhd'],cwd=cwd,check=True)
 args=['ghdl','-r','--std=08','-fsynopsys','tb_block_compare24']+[f'-g{k}={str(v).lower()}' for k,v in case.items()]+['--assert-level=error']
 q=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
 print('CASE '+' '.join(args[5:]),flush=True);print(q.stdout+q.stderr,end='',flush=True)
 if q.returncode or 'PASS compare' not in q.stdout:raise SystemExit(f'FAIL {case}: exit {q.returncode}')
print(f'PASS all {len(cases)} block-compare cases',flush=True)
