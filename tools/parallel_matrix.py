"""Run independent GHDL cases in isolated work libraries, preserving ordered output."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

def run_matrix(root, entity, cases, marker, workers=4, work_name='verification_parallel'):
 root=Path(root).resolve();cases=list(cases)
 def worker(index):
  cwd=root/work_name/f'{entity}_{index}';cwd.mkdir(parents=True,exist_ok=True)
  for f in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
   subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(root/'fpga/G80A_eZ80'/f'{f}_ez80.vhd')],cwd=cwd,check=True,capture_output=True,text=True)
  records=[]
  for number in range(index,len(cases),workers):
   case=cases[number]
   subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(root/'sim'/f'{entity}.vhd')],cwd=cwd,check=True,capture_output=True,text=True)
   args=['ghdl','-r','--std=08','-fsynopsys',entity]+[f'-g{k}={str(v).lower()}' for k,v in case.items()]+['--assert-level=error']
   q=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
   output='CASE '+' '.join(args[5:])+'\n'+q.stdout+q.stderr
   if q.returncode or marker not in q.stdout:raise RuntimeError(f'{entity} failed: {case}\n{output}')
   records.append((number,output))
  return records
 with ThreadPoolExecutor(max_workers=workers) as pool:
  records=[record for group in pool.map(worker,range(workers)) for record in group]
 assert len(records)==len(cases)
 for _,output in sorted(records):print(output,end='',flush=True)
 return len(records)
