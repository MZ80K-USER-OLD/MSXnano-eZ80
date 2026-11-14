"""Run the additional checks; capture and commit each complete log atomically."""
from pathlib import Path
import subprocess,os,json
r=Path(__file__).resolve().parent.parent
for command,name,count in [(['python3','tools/run_native_absolute281.py'],'native_absolute',168),(['python3','tools/run_block_io_compat.py'],'compat',32),(['bash','run_indexed_cb_suffix.sh'],'suffix',8),(['bash','run_size_smoke.sh'],'size',6),(['python3','tools/run_exchange_compat30.py'],'exchange_compat',4),(['python3','tools/run_stack_compat31.py'],'stack_compat',8)]:
 p=subprocess.run(command,cwd=r,text=True,capture_output=True)
 assert p.returncode==0,p.stdout[-4000:]+p.stderr[-4000:]
 path=r/f'test_results_{name}_v31.log'
 if name in ('native_absolute','compat','exchange_compat','stack_compat'):
  assert path.read_text().count('simulation stopped')==count
 else:
  assert p.stdout.count('simulation stopped')==count
  temp=path.with_suffix('.tmp');temp.write_text(p.stdout+p.stderr);os.replace(temp,path)
 print('PASS additional',name,count,flush=True)
