from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent.parent
for n in ['t80','t80_mcode','g80a']:
 p=r/'fpga/G80A_eZ80'/(n+'_ez80.vhd');assert p.read_bytes()==(r/'doc/r13_1_mixed_baseline'/(p.name+'.txt')).read_bytes(),p
subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(r/'doc/R14_MIXED.patch')],cwd=r,check=True)
print('PASS R14 mixed frame patch replay from exact R13.1')
