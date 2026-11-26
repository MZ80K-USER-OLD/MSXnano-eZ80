from pathlib import Path
import os,subprocess,sys
R=Path(__file__).resolve().parents[1]
def run(name,env=None):
 subprocess.run([sys.executable,str(R/'tools'/name)],cwd=R,env=env,check=True)
run('synthesize_r30.py')
run('verify_decode_width_r24.py')
run('verify_recovery_r29_1.py')
env=os.environ.copy();env.pop('STRESS',None)
env['NAMES']=','.join(s.split()[0]for s in(R/'RUNALL.BAT').read_text().splitlines()if s.strip())
run('verify_differential_r27.py',env)
env['STRESS']='1';env['NAMES']='EZ80MEM,EZ80ALU,EZ80LEA,EZ80LDH,EZ80LDX,EZ80MIX,EZ80MAD'
run('verify_differential_r27.py',env)
run('verify_release_r30.py')
