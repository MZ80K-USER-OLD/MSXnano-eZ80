"""Run each block-transfer case and require its explicit PASS record."""
import itertools
import subprocess
from pathlib import Path
cwd=Path(__file__).resolve().parent.parent/'verification'
cases=[]
for repeat,down,short,addr,wait in itertools.product((False,True),(False,True),(False,True),range(3),(False,True)):
 for count in (range(1) if repeat else range(4)):
  cases.append(dict(REPEATING=repeat,DECREMENTING=down,SHORT_MODE=short,ADDRESS_CASE=addr,INSERT_WAIT=wait,COUNT_CASE=count))
for down,addr,wait in itertools.product((False,True),range(3),(False,True)):
 cases.append(dict(REPEATING=True,HIGH_REPEAT=True,DECREMENTING=down,ADDRESS_CASE=addr,INSERT_WAIT=wait))
for case in cases:
 subprocess.run(['ghdl','-a','--std=08','-fsynopsys','../sim/tb_block_transfer24.vhd'],cwd=cwd,check=True)
 args=['ghdl','-r','--std=08','-fsynopsys','tb_block_transfer24']+[f'-g{k}={str(v).lower()}' for k,v in case.items()]+['--assert-level=error']
 q=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
 print('CASE '+' '.join(args[5:]),flush=True);print(q.stdout+q.stderr,end='',flush=True)
 if q.returncode or 'PASS block' not in q.stdout:raise SystemExit(f'FAIL {case}: exit {q.returncode}')
print(f'PASS all {len(cases)} block-transfer cases',flush=True)
