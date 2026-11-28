from pathlib import Path
import os,subprocess,sys
R=Path(__file__).resolve().parents[1]
def run(name,env=None):
 subprocess.run([sys.executable,str(R/'tools'/name)],cwd=R,env=env,check=True)
run('synthesize_r32.py')
run('verify_decode_width_r24.py')
run('verify_class_structure_r32.py')
run('verify_mcode_r32.py')
env=os.environ.copy();env.pop('STRESS',None)
env['NAMES']=','.join(s.split()[0]for s in(R/'RUNALL.BAT').read_text().splitlines()if s.strip())
env['NAMES']+=',EZ80MX0,EZ80MX1,EZ80MX2,EZ80MA1,EZ80MR4'
run('verify_differential_r32.py',env)
env['STRESS']='1';env['NAMES']='EZ80MEM,EZ80ALU,EZ80MUL,EZ80LEA,EZ80LDH,EZ80LDX,EZ80MIX,EZ80MAD,EZ80MB,EZ80BLK,EZ80DEC,EZ80IRQ,EZ80NMI'
run('verify_differential_r32.py',env)
run('verify_release_r32.py')
