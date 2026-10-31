from pathlib import Path
from itertools import product
import subprocess,os,json
r=Path(__file__).resolve().parent.parent;g=os.environ.get('GHDL','ghdl')
def invoke(args,w):
 p=subprocess.run([g]+args,cwd=w,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
 return p.stdout+p.stderr
def compile_cpu(w):
 for folder,suffix in [('G80A',''),('G80A_eZ80','_ez80')]:
  for f in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
   invoke(['-a','--std=08','-fsynopsys',str(r/'fpga'/folder/(f+suffix+'.vhd'))],w)
logs=[]
for n,vals in enumerate(product(('false','true'),repeat=4)):
 w=r/'verification_guard_cases'/str(n);w.mkdir(parents=True,exist_ok=True);compile_cpu(w)
 invoke(['-a','--std=08','-fsynopsys',str(r/'sim/tb_guard_compat341.vhd')],w)
 ext,wait,seed,carry=vals
 args=['-r','--std=08','-fsynopsys','tb_guard_compat341',f'-gEXTENSIONS={ext}',f'-gINSERT_WAIT={wait}',f'-gSEED={seed}',f'-gCARRY_IN={carry}','--assert-level=error']
 t=invoke(args,w);assert 'PASS locked boot' in t
 logs.append('CASE '+' '.join(args[5:])+'\n'+t)
(r/'test_results_guard_compat_v34_1.log').write_text(''.join(logs))
print('PASS guarded Z80 comparison',len(logs),flush=True)
w=r/'verification_bios_guarded/run';w.mkdir(parents=True,exist_ok=True);compile_cpu(w)
invoke(['-a','--std=08','-fsynopsys',str(r/'sim/tb_bios_compare341.vhd')],w)
t=invoke(['-r','--std=08','-fsynopsys','tb_bios_compare341','--assert-level=error'],w)
assert 'PASS BIOS comparison interval' in t
(r/'test_results_bios_guard_v34_1.log').write_text(t)
(r/'verification_guard_v34_1.json').write_text(json.dumps(dict(compatibility_cases=16,bios_interval_ms=20,bios_cases=1,full_boot_verified=False),indent=2)+'\n')
print('PASS BIOS 20 ms CPU comparison; not a completed BIOS boot',flush=True)
