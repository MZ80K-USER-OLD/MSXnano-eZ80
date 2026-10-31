import subprocess,itertools
from pathlib import Path
cwd=Path(__file__).resolve().parent.parent/'verification'
for r,edge,c,s,w in itertools.product(range(2),range(3),range(32),('false','true'),('false','true')):
 b,a,d=((1,0,-128),(255,65535,127),(127,32768,1))[edge]
 args=['ghdl','-r','--std=08','-fsynopsys','tb_indexed_cb24',f'-gREG_SELECT={r}',f'-gBANK={b}',f'-gSTACK_TOP={a}',f'-gDISPLACEMENT={d}',f'-gCONDITION={c}',f'-gTAKEN={s}',f'-gINSERT_WAIT={w}','--assert-level=error']
 subprocess.run(['ghdl','-a','--std=08','-fsynopsys','../sim/tb_indexed_cb24.vhd'],cwd=cwd,check=True)
 q=subprocess.run(args,cwd=cwd,text=True,capture_output=True);assert q.returncode==0 and 'PASS indexed CB' in q.stdout,(args,q.stdout,q.stderr)
 print('CASE '+' '.join(args[5:]),flush=True);print(q.stdout+q.stderr,end='',flush=True)
print('PASS 768 indexed CB cases with per-case completion checks')
