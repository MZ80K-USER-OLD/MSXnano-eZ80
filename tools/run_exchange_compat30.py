from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parent.parent;w=r/'verification_exchange_compat30';w.mkdir(exist_ok=True)
for folder,suffix in [('G80A',''),('G80A_eZ80','_ez80')]:
 for f in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
  subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(r/'fpga'/folder/(f+suffix+'.vhd'))],cwd=w,check=True,capture_output=True)
subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(r/'sim/tb_exchange_compat30.vhd')],cwd=w,check=True,capture_output=True)
logs=[]
for alt in ('false','true'):
 for wait in ('false','true'):
  args=['ghdl','-r','--std=08','-fsynopsys','tb_exchange_compat30',f'-gALT_FIRST={alt}',f'-gINSERT_WAIT={wait}','--assert-level=error']
  p=subprocess.run(args,cwd=w,text=True,capture_output=True);out=p.stdout+p.stderr
  assert p.returncode==0 and 'PASS default EX' in out,out[-3000:]
  logs.append('CASE '+' '.join(args[5:])+'\n'+out)
f=r/'test_results_exchange_compat_v32.log';tmp=f.with_suffix('.tmp');tmp.write_text(''.join(logs));os.replace(tmp,f)
print('PASS default exchange compatibility',len(logs),flush=True)
