from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parent.parent;w=r/'verification_phase_compat32';w.mkdir(exist_ok=True)
for folder,suffix in [('G80A',''),('G80A_eZ80','_ez80')]:
 for f in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
  subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(r/'fpga'/folder/(f+suffix+'.vhd'))],cwd=w,check=True,capture_output=True)
subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(r/'sim/tb_phase_compat32.vhd')],cwd=w,check=True,capture_output=True)
logs=[]
from itertools import product
for alt,flag,wait in product(('false','true'),repeat=3):
 args=['ghdl','-r','--std=08','-fsynopsys','tb_phase_compat32',f'-gSEED={alt}',f'-gCARRY_IN={flag}',f'-gINSERT_WAIT={wait}','--assert-level=error']
 p=subprocess.run(args,cwd=w,text=True,capture_output=True);out=p.stdout+p.stderr
 assert p.returncode==0 and 'PASS default RLD' in out,out[-3000:]
 logs.append('CASE '+' '.join(args[5:])+'\n'+out)
f=r/'test_results_phase_compat_v32.log';tmp=f.with_suffix('.tmp');tmp.write_text(''.join(logs));os.replace(tmp,f)
print('PASS default RLD/EX SP compatibility',len(logs),flush=True)
