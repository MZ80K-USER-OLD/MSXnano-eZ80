from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';assert p.read_bytes()==(r/'doc/r13_bus_baseline/t80_ez80.vhd.txt').read_bytes()
subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(r/'doc/R13_1_REGISTERED_BUS.patch')],cwd=r,check=True)
print('PASS R13.1 registered bus patch replay')
