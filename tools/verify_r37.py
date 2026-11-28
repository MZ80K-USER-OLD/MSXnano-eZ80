from pathlib import Path
import os,sys,subprocess,json
R=Path(__file__).resolve().parents[1]
def run(path,env=None,allow_known_fuse_mismatch=False):
 a=subprocess.run([sys.executable,str(R/path)],cwd=R,env=env)
 assert a.returncode==0 or (allow_known_fuse_mismatch and a.returncode==1),str(path)
run('tools/synthesize_r37.py');run('fuse_test/tools/build_dut.py');run('tools/verify_scope_r37.py');run('tools/verify_ir_flags_r37.py')
for args in [['--match','^ED_(57|5F)_','--name','ldair_r37'],['--name','full_r37'],['--events-only','--name','events_r37']]:
 a=subprocess.run([sys.executable,str(R/'fuse_test/tools/run_fuse.py')]+args,cwd=R);assert a.returncode in ([0] if '--match' in args else [0,1])
run('fuse_test/tools/audit_suite.py');run('fuse_test/tools/analyze_r37.py');run('fuse_test/tools/verify_comparator_r37.py')
env=os.environ.copy();env.pop('NAMES',None);env.pop('STRESS',None);env.pop('OUT_TAG',None);env['CPU_DIV']='4'
run('tools/verify_com_r37.py',env)
env['STRESS']='1';env['NAMES']='EZ80MEM,EZ80MIX,EZ80MAD,EZ80MB,EZ80IRQ,EZ80IM2,EZ80NMI,EZ80MX0,EZ80MX1,EZ80MX2,EZ80MA1,EZ80MR4';run('tools/verify_com_r37.py',env)
env['NAMES']='EZ80IRF';env['OUT_TAG']='irf';env.pop('STRESS');run('tools/verify_com_r37.py',env);env['STRESS']='1';run('tools/verify_com_r37.py',env)
run('tools/verify_ir_com_negative_r37.py');run('tools/verify_release_r37.py')
