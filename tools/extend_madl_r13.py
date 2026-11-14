from pathlib import Path
import subprocess,shutil
r=Path(__file__).resolve().parent.parent
for n in ['t80','t80_pack','t80_mcode','g80a']:
 p=r/'fpga/G80A_eZ80'/(n+'_ez80.vhd');assert p.read_bytes()==(r/'doc/r12_madl_baseline'/(p.name+'.txt')).read_bytes(),p
subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(r/'doc/R13_MADL.patch')],cwd=r,check=True)
print('PASS applied R13 MADL patch to exact R12 sources')
