from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parent.parent
w=r/'verification_compat';w.mkdir(exist_ok=True)
for folder,suffix in [('G80A',''),('G80A_eZ80','_ez80')]:
 for f in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
  subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(r/'fpga'/folder/(f+suffix+'.vhd'))],cwd=w,check=True,capture_output=True)
subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(r/'sim/tb_block_io_compat.vhd')],cwd=w,check=True,capture_output=True)
logs=[]
for op in range(8):
 for b in [0,3]:
  for wait in ['false','true']:
   args=['ghdl','-r','--std=08','-fsynopsys','tb_block_io_compat',f'-gOP={op}',f'-gINITIAL_B={b}',f'-gINSERT_WAIT={wait}','--assert-level=error']
   p=subprocess.run(args,cwd=w,capture_output=True,text=True);out=p.stdout+p.stderr
   assert p.returncode==0 and 'PASS legacy' in out,out[-3000:]
   logs.append('CASE '+' '.join(args[5:])+'\n'+out)
path=r/'test_results_compat_v32.log';tmp=path.with_suffix('.tmp');tmp.write_text(''.join(logs));os.replace(tmp,path);print('legacy compatibility PASS',len(logs),flush=True)
