from pathlib import Path
from itertools import product
from parallel_matrix import run_matrix
root=Path(__file__).resolve().parent.parent
absolute_cases=[dict(zip(('NATIVE_ADL','SUFFIX','TARGET','BOUNDARY','LOADING','INSERT_WAIT'),v)) for v in product((False,True),range(4),range(7),range(3),(False,True),(False,True))]
control_cases=[]
for native,long,explicit in product((False,True),(False,True),(False,True)):
 if not explicit and native!=long:continue
 for kind in (0,1):
  for cond in range(9):
   for taken in ((False,True) if cond<8 else (True,)):
    for ret in ((False,True) if kind==1 and taken and cond<8 else (True,)):
     for boundary,wait in product(range(3),(False,True)):
      control_cases.append(dict(NATIVE_ADL=native,LONG_TARGET=long,EXPLICIT_SUFFIX=explicit,KIND=kind,CONDITION=cond,TAKEN=taken,RET_TAKEN=ret,BOUNDARY=boundary,INSERT_WAIT=wait))
 for reg,boundary,wait in product(range(3),range(3),(False,True)):
  control_cases.append(dict(NATIVE_ADL=native,LONG_TARGET=long,EXPLICIT_SUFFIX=explicit,KIND=2,REG_SELECT=reg,BOUNDARY=boundary,INSERT_WAIT=wait))
if __name__=='__main__':
 print('PASS absolute matrix',run_matrix(root,'tb_suffix_absolute281',absolute_cases,'PASS absolute V2'))
 print('PASS control matrix',run_matrix(root,'tb_suffix_control281',control_cases,'PASS V2'))
