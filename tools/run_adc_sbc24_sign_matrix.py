"""Opposite-sign operands: positive minus negative, and carry crossing the signed range."""
import itertools
import subprocess
from pathlib import Path
cwd=Path(__file__).resolve().parent.parent/'verification_sign'
cwd.mkdir(parents=True,exist_ok=True)
root=cwd.parent
for f in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
 subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(root/'fpga/G80A_eZ80'/f'{f}_ez80.vhd')],cwd=cwd,check=True)
count=0
for sub,vector,carry,short,wait in itertools.product((False,True),range(2),(False,True),(False,True),(False,True)):
 subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(root/'sim/tb_adc_sbc24_sign.vhd')],cwd=cwd,check=True)
 args=['ghdl','-r','--std=08','-fsynopsys','tb_adc_sbc24_sign',f'-gSUBTRACTING={str(sub).lower()}',f'-gVECTOR={vector}',f'-gCARRY_IN={str(carry).lower()}',f'-gSHORT_MODE={str(short).lower()}',f'-gINSERT_WAIT={str(wait).lower()}','--assert-level=error']
 q=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
 print('SIGN CASE '+' '.join(args[5:]),flush=True);print(q.stdout+q.stderr,end='',flush=True)
 if q.returncode or 'PASS ADC/SBC24' not in q.stdout:raise SystemExit(f'FAIL {(sub,vector,carry,short,wait)}: exit {q.returncode}')
 count+=1
print(f'PASS all {count} opposite-sign ADC/SBC cases',flush=True)
