"""R36 verification entry point. Requires GHDL and Icarus in the environment."""
from pathlib import Path
import subprocess,sys,os
R=Path(__file__).resolve().parents[1]
def run(name,env=None):subprocess.run([sys.executable,str(R/'tools'/name)],cwd=R,env=env,check=True)
run('synthesize_r36.py')
run('verify_scope_r36.py')
run('verify_mode_byte_r36.py')
run('verify_frame_gate_r36.py')
run('verify_input_capture_r36.py')
run('verify_decode_width_r24.py')
e=os.environ.copy();e.pop('STRESS',None);e.pop('NAMES',None);e['CPU_DIV']='4'
run('verify_differential_r36.py',e)
e['STRESS']='1';e['NAMES']='EZ80MEM,EZ80MIX,EZ80MAD,EZ80MB,EZ80IRQ,EZ80IM2,EZ80NMI,EZ80MX0,EZ80MX1,EZ80MX2,EZ80MA1,EZ80MR4'
run('verify_differential_r36.py',e)
run('verify_release_r36.py')
