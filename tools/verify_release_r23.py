"""Reproduce R23 checks. GOWIN synthesis, place/route and board tests are external."""
from pathlib import Path
import subprocess,sys,os,shutil
r=Path(__file__).resolve().parent.parent;loc=r.parents[1]
for key,rel,fallback in [('GHDL','local-ghdl/usr/bin/ghdl','ghdl'),('IVERILOG','local-iverilog/usr/bin/iverilog','iverilog'),('VVP','local-iverilog/usr/bin/vvp','vvp')]:
 os.environ.setdefault(key,str(loc/rel)if(loc/rel).is_file()else(shutil.which(fallback)or fallback))
if(loc/'local-ghdl/usr/lib/ghdl/mcode/vhdl').exists():os.environ.setdefault('GHDL_PREFIX',str(loc/'local-ghdl/usr/lib/ghdl/mcode/vhdl'))
if(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl').exists():os.environ.setdefault('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'))
for n in ['synthesize_r22','verify_irx_r23','verify_tstio_r23','verify_tstio_operand_r23','verify_io_excluded_r23','verify_irx_com_r23','verify_tio_com_r23','verify_mem_r4','verify_mr6_r22_4','verify_wait_monitor_r22_3','verify_vhdl93_r11_1']:
 subprocess.run([sys.executable,str(r/'tools'/(n+'.py'))],cwd=r,check=True)
iv=[os.environ['IVERILOG']]+(['-B',os.environ['IVL_ROOT']]if'IVL_ROOT'in os.environ else[])
w=r/'verification_r23';w.mkdir(exist_ok=True);v=w/'locked74.vvp'
subprocess.run(iv+['-g2012','-s','tb_locked74_r23','-o',str(v),str(r/'sim/tb_locked74_r23.sv'),str(r/'verification/cpu_1.v')],cwd=r,check=True)
p=subprocess.run([os.environ['VVP'],str(v)],cwd=r,capture_output=True,text=True,check=True)
(w/'locked74.log').write_text(p.stdout+p.stderr);assert 'PASS locked ED74 NEG alias'in p.stdout
print('PASS R23 simulation checks; GOWIN/area/STA/board not certified')
