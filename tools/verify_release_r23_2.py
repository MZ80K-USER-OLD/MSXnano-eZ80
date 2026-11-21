from pathlib import Path
import os,subprocess,sys
r=Path(__file__).resolve().parent.parent;loc=r.parents[1];env=os.environ.copy()
for k,p in dict(GHDL='local-ghdl/usr/bin/ghdl',GHDL_PREFIX='local-ghdl/usr/lib/ghdl/mcode/vhdl',IVERILOG='local-iverilog/usr/bin/iverilog',IVL_ROOT='local-iverilog/usr/lib/x86_64-linux-gnu/ivl',VVP='local-iverilog/usr/bin/vvp').items():
    if (loc/p).exists():env.setdefault(k,str(loc/p))
for n in ['synthesize_r22.py','verify_vhdl93_r11_1.py','verify_mcode_r23_2.py','verify_io_removed_r23_2.py','verify_mem_r4.py','verify_mr4_r21_3.py','verify_io_nop_com_r23_2.py']:
    print('Running',n,flush=True);subprocess.run([sys.executable,str(r/'tools'/n)],cwd=r,env=env,check=True)
print('PASS local R23.2 checks; GOWIN and board verification required')
