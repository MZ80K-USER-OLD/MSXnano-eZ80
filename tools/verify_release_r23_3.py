from pathlib import Path
import os,subprocess,sys
r=Path(__file__).resolve().parent.parent;loc=r.parents[1];env=os.environ.copy()
for k,p in dict(GHDL='local-ghdl/usr/bin/ghdl',GHDL_PREFIX='local-ghdl/usr/lib/ghdl/mcode/vhdl',IVERILOG='local-iverilog/usr/bin/iverilog',IVL_ROOT='local-iverilog/usr/lib/x86_64-linux-gnu/ivl',VVP='local-iverilog/usr/bin/vvp').items():
    if (loc/p).exists():env.setdefault(k,str(loc/p))
for n in ['synthesize_r22.py','verify_vhdl93_r11_1.py','verify_bridge_r23_3.py','verify_mem_r4.py','verify_mr4_r21_3.py','verify_io_nop_com_r23_2.py','verify_im0_com_r19.py']:
    e=env.copy()
    if n=='verify_im0_com_r19.py':e['CASE_INDEX']='0,1'
    print('Running',n,flush=True);subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,env=e,check=True)
print('PASS R23.3 local checks; GOWIN and board verification required')
