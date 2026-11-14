"""Execute the explicit regression plan in isolated GHDL libraries; save logs atomically."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,os,subprocess,threading,time
root=Path(__file__).resolve().parent.parent
cases=json.loads((root/'tools/regression_cases_v32.json').read_text())
workers=int(os.environ.get('GHDL_WORKERS','8'));assert 1<=workers<=16
entities=sorted({x['entity'] for x in cases})
lock=threading.Lock();done=0;started=time.monotonic()
def invoke(args,cwd):
 q=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
 if q.returncode:raise RuntimeError(f'{args}\n{q.stdout}\n{q.stderr}')
 return q.stdout+q.stderr

def worker(i):
 global done
 cwd=root/'verification_full'/str(i);cwd.mkdir(parents=True,exist_ok=True)
 for folder,suffix in (('G80A',''),('G80A_eZ80','_ez80')):
  for f in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
   invoke(['ghdl','-a','--std=08','-fsynopsys',str(root/'fpga'/folder/(f+suffix+'.vhd'))],cwd)
 for entity in entities:invoke(['ghdl','-a','--std=08','-fsynopsys',str(root/'sim'/(entity+'.vhd'))],cwd)
 records=[]
 for n in range(i,len(cases),workers):
  item=cases[n];entity=item['entity']
  invoke(['ghdl','-a','--std=08','-fsynopsys',str(root/'sim'/(entity+'.vhd'))],cwd)
  args=item.get('args')
  if args is None:args=['--std=08','-fsynopsys',entity]+[f'-g{k}={str(v).lower()}' for k,v in item['case'].items()]+['--assert-level=error']
  output=invoke(['ghdl','-r']+args,cwd)
  if 'PASS' not in output or 'simulation stopped' not in output:raise RuntimeError(f'Incomplete case {n}: {args}\n{output}')
  marker='SIGN CASE ' if item['sign'] else 'CASE '
  records.append((n,'TEST '+entity+'\n'+marker+' '.join(args[args.index(entity)+1:])+'\n'+output,str(cwd),args))
  with lock:
   done+=1
   if done%500==0:print(f'Completed {done}/{len(cases)} cases',flush=True)
 return records

with ThreadPoolExecutor(max_workers=workers) as pool:records=[r for group in pool.map(worker,range(workers)) for r in group]
records.sort();assert len(records)==len(cases)==25127
wave={}
for _,_,cwd,args in records:
 for arg in args:
  if arg.startswith('--vcd='):wave[arg.split('=',1)[1]]=str(Path(cwd)/arg.split('=',1)[1])
wave_output=invoke(['python3',str(root/'tools/check_long_ld.py'),wave['long_ld_false.vcd'],wave['long_ld_true.vcd']],root)
text=''.join(r[1] for r in records)+wave_output+'PASS all 25127 regression cases\n'
assert text.count('simulation stopped')==25127
path=root/'test_results_v32.log';tmp=path.with_suffix('.tmp');tmp.write_text(text);os.replace(tmp,path)
for entity,label in (('tb_decimal32','decimal'),('tb_restart32','restart'),('tb_relative32','relative'),('tb_stack31','stack'),('tb_exchange_sp30','exchange_sp'),('tb_mbase_irq29','mbase_irq'),('tb_isa_slots29','isa_slots'),('tb_mbase_bus29','mbase_bus'),('tb_mbase_absolute29','mbase_absolute'),('tb_mbase_control29','mbase_control'),('tb_adc_sbc24','adc_sbc'),('tb_adc_sbc24_sign','adc_sbc_sign'),('tb_block_io24','block_io'),('tb_suffix_width28','suffix_width'),('tb_suffix_absolute281','absolute_v2'),('tb_suffix_control281','control_v2'),('tb_native_call_v2_281','nested_v2')):
 content=''.join(record[1] for record in records if cases[record[0]]['entity']==entity)
 path=root/f'test_results_{label}_v32.log';tmp=path.with_suffix('.tmp');tmp.write_text(content);os.replace(tmp,path)
manifest=dict(passed=len(records),workers=workers,elapsed_seconds=round(time.monotonic()-started,2),wave_check='PASS',source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'fpga/G80A_eZ80').glob('*.vhd')})
(root/'verification_result_v32.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PASS 25127 regression cases and waveform checks; complete logs saved',flush=True)
