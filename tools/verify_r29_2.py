from pathlib import Path
import subprocess,sys,os
R=Path(__file__).resolve().parents[1]
for n in ['synthesize_r29_2.py','verify_recovery_r29_1.py','verify_input_frame_r29.py','verify_strobes_r28.py','verify_vdp_io_r28.py','selftest_gowin_cpu_r29_2.py']:
 subprocess.run([sys.executable,str(R/'tools'/n)],cwd=R,check=True)
for stress in [False,True]:
 env=os.environ.copy();env['NAMES']='EZ80MEM,EZ80MIX,EZ80MAD,EZ80IRQ'
 if stress:env['STRESS']='1'
 else:env.pop('STRESS',None)
 subprocess.run([sys.executable,str(R/'tools/verify_differential_r27.py')],cwd=R,env=env,check=True)
subprocess.run([sys.executable,str(R/'tools/verify_release_r29_2.py')],cwd=R,check=True)
