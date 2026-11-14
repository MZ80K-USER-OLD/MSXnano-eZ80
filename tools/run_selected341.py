from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,os
r=Path(__file__).resolve().parent.parent;g=os.environ.get('GHDL','ghdl')
cases=json.loads((r/'tools/regression_cases_v34_1_selected.json').read_text())
def worker(n):
 w=r/'verification_selected341'/str(n);w.mkdir(parents=True,exist_ok=True)
 def run(args):return subprocess.run([g]+args,cwd=w,text=True,capture_output=True)
 for folder,suffix in [('G80A',''),('G80A_eZ80','_ez80')]:
  for f in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
   p=run(['-a','--std=08','-fsynopsys',str(r/'fpga'/folder/(f+suffix+'.vhd'))]);assert p.returncode==0,p.stderr
 out=[]
 for i in range(n,len(cases),4):
  x=cases[i];entity=x['entity'];p=run(['-a','--std=08','-fsynopsys',str(r/'sim'/(entity+'.vhd'))]);assert p.returncode==0,p.stderr
  args=x.get('args')
  if args is None:args=['--std=08','-fsynopsys',entity]+[f'-g{k}={str(v).lower()}' for k,v in x['case'].items()]+['--assert-level=error']
  p=run(['-r']+args);t=p.stdout+p.stderr
  out.append(dict(index=i,passed=p.returncode==0 and 'PASS' in t and 'simulation stopped' in t,case=x,output=t))
 return out
with ThreadPoolExecutor(max_workers=4) as pool:out=sorted([v for group in pool.map(worker,range(4)) for v in group],key=lambda x:x['index'])
(r/'test_results_selected_v34_1.log').write_text(''.join('CASE '+json.dumps(x['case'])+'\n'+x['output'] for x in out))
bad=[x for x in out if not x['passed']]
(r/'verification_selected_v34_1.json').write_text(json.dumps(dict(passed=len(out)-len(bad),failed=bad,total=len(out)),indent=2)+'\n')
print('Selected cases',len(out)-len(bad),'PASS',len(bad),'FAIL')
for x in bad:print(x['index'],x['case'],x['output'][-1500:])
if bad:raise SystemExit(1)
