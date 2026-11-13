from pathlib import Path
import subprocess,os,itertools,json
r=Path(__file__).resolve().parent.parent;w=r/'verification';g=os.environ['GHDL']
for n in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
 subprocess.run([g,'-a','--std=08','-fsynopsys',str(r/'fpga/G80A'/(n+'.vhd'))],cwd=w,check=True)
subprocess.run([g,'-a','--std=08','-fsynopsys',str(r/'sim/tb_locked_r1.vhd')],cwd=w,check=True)
rows=[]
for vals in itertools.product(('false','true'),repeat=4):
 args=[f'-g{k}={v}' for k,v in zip(('EXTENSIONS','INSERT_WAIT','SEED','CARRY_IN'),vals)]
 a=subprocess.run([g,'-r','--std=08','-fsynopsys','tb_locked_r1']+args+['--assert-level=error'],cwd=w,text=True,capture_output=True)
 assert a.returncode==0 and 'PASS locked boot' in a.stdout+a.stderr,a.stdout+a.stderr
 rows.append({'args':args,'output':a.stdout+a.stderr})
(r/'verification_locked_r18_3_result.json').write_text(json.dumps({'fresh_runs':len(rows),'cases':rows},indent=2)+'\n')
print('PASS locked T80 compatibility',len(rows))
