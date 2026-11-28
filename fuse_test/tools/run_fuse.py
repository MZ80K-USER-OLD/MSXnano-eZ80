"""Execute independent FUSE input states on R37 RTL. Expected data never enters the simulator."""
from pathlib import Path
import argparse,json,re,subprocess,os,hashlib,collections,itertools
from compare import compare_record
R=Path(__file__).resolve().parents[1];FIELDS='AF BC DE HL AF2 BC2 DE2 HL2 IX IY SPL PC I R IFF1 IFF2 IM HALTED ADL MBASE MADL SPS'.split()
EXCLUDED={'SLP','IN0','OUT0','INIM','INDM','INIMR','INDMR','OTIM','OTDM','OTIMR','OTDMR','INI2','IND2','INI2R','IND2R','OUTI2','OUTD2','OTI2R','OTD2R'}
UNIMPLEMENTED={'INIRX','INDRX','OTIRX','OTDRX'}
def blocks(p):
 with p.open() as f:
  while True:
   name=f.readline().strip()
   if not name:break
   v=f.readline().split();q=f.readline().split();m=f.readline().split();assert len(v)==12 and len(q)==7 and len(m)==4
   state=dict(zip(FIELDS[:12],[int(x,16) for x in v]));state.update(I=int(q[0],16),R=int(q[1],16),IFF1=int(q[2]),IFF2=int(q[3]),IM=int(q[4]),HALTED=int(q[5]),ADL=int(m[0]),MBASE=int(m[1],16),MADL=int(m[2]),SPS=int(m[3],16))
   mem={}
   for line in f:
    if line.strip()=='-1':break
    a,b,end=line.split();assert end=='-1';mem[a]=int(b,16)
   assert f.readline()=='\n';yield dict(id=name,state=state,memory=mem)
def read_raw(p,cases):
 cur=None
 for line in p.open():
  v=line.split()
  if not v:continue
  if v[0]=='BEGIN':cur=dict(index=int(v[1]),state={},memory={},events=[],raw_events=[])
  elif v[0]=='STATE':
   assert len(v)==23
   cur['state']={k:None if re.search('[xz]',x,re.I) else int(x,16) for k,x in zip(FIELDS,v[1:])}
   if cur['state']['ADL']==0 and cur['state']['PC'] is not None:cur['state']['PC']&=65535
  elif v[0]=='MEM':cur['memory'][f'{int(v[1],16):06x}']=None if re.search('[xz]',v[2],re.I) else int(v[2],16)
  elif v[0]=='EV':
   kind=v[1];a=None if re.search('[xz]',v[2],re.I) else int(v[2],16);val=None if re.search('[xz]',v[3],re.I) else int(v[3],16)
   cur['raw_events'].append(dict(kind=kind,address=a,value=val))
  elif v[0]=='END':
   cur['status']=int(v[1]);cur['cycles']=int(v[2]);c=cases[cur['index']];s=c['initial']
   codeaddr={((s['PC']+i)&0xffffff) if s['ADL'] else (s['MBASE']<<16)|((s['PC']+i)&65535) for i in range(len(c['code']))}
   cur['events']=[e for e in cur['raw_events'] if e['kind']!='IF' and not(e['kind']=='MR' and e['address'] in codeaddr)]
   yield cur;cur=None
 assert cur is None,'truncated DUT output'
def main():
 p=argparse.ArgumentParser();p.add_argument('--match',default='.*');p.add_argument('--limit',type=int);p.add_argument('--name',default='full_r37');p.add_argument('--max-cycles',type=int,default=4096);p.add_argument('--include-excluded',action='store_true');p.add_argument('--events-only',action='store_true');a=p.parse_args()
 cat={x['key']:x for x in json.loads((R/'suite/opcode_catalog.json').read_text())}
 cases=[];expected=[];traces=[];skips=[]
 for c,e,t in zip((json.loads(l) for l in (R/'suite/cases.jsonl').open()),blocks(R/'suite/tests.expected'),(json.loads(l) for l in (R/'suite/events.expected.jsonl').open())):
  assert c['id']==e['id']==t['id']
  if not re.search(a.match,c['id']):continue
  if a.events_only and c['coverage']!='external_event':continue
  mnemonic=cat.get(c['instruction'],{}).get('mnemonic','external')
  reason='external_event_separate_batch' if c['events'] or c['coverage']=='external_event' else 'policy_excluded' if mnemonic in EXCLUDED else 'not_implemented' if mnemonic in UNIMPLEMENTED else None
  if a.events_only:reason=None
  if reason and (reason=='external_event_separate_batch' or not a.include_excluded):skips.append(dict(id=c['id'],reason=reason,mnemonic=mnemonic));continue
  if a.limit is not None and len(cases)>=a.limit:continue
  cases.append(c);expected.append(e);traces.append(t)
 assert cases,'no eligible cases selected'
 out=R/'results'/a.name;out.mkdir(parents=True,exist_ok=True)
 (out/'result.json').unlink(missing_ok=True)
 stim=out/'stimulus.txt'
 with stim.open('w') as f:
  for i,c in enumerate(cases):
   f.write(f'{i:x} {c["steps"]:x} {c["io_seed"]:x} {len(c["memory"]):x} {len(c["code"]):x} {int(c["instruction"] in {"ED_B0","ED_B1","ED_B2","ED_B3","ED_B8","ED_B9","ED_BA","ED_BB"}):x}\n')
   if a.events_only:f.write(' '.join(f'{c["events"].get(str(j),0):x}' for j in range(3))+'\n')
   f.write(' '.join(f'{c["initial"][k]:x}' for k in FIELDS)+'\n')
   for addr,v in c['memory'].items():f.write(f'{addr} {v:x}\n')
 (out/'selected.json').write_text(json.dumps([dict(id=c['id'],instruction=c['instruction'],coverage=c['coverage']) for c in cases],indent=2)+'\n')
 (out/'excluded.json').write_text(json.dumps(skips,indent=2)+'\n')
 iv=os.environ.get('IVERILOG','iverilog');cmd=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])+['-g2012','-I',str(R/'build'),'-s','tb_fuse','-o',str(out/'fuse.vvp'),str(R/'sim'/('tb_events.sv' if a.events_only else 'tb_fuse.sv')),str(R/'build/dut.v')]
 z=subprocess.run(cmd,capture_output=True,text=True);assert not z.returncode,z.stderr
 z=subprocess.run([os.environ.get('VVP','vvp'),str(out/'fuse.vvp'),'+INPUT='+str(stim),'+OUTPUT='+str(out/'raw.txt'),f'+MAX_CYCLES={a.max_cycles}'],capture_output=True,text=True,timeout=7200)
 (out/'simulation.log').write_text(z.stdout+z.stderr);assert not z.returncode,z.stdout+z.stderr
 rows=[];actual=out/'dut_actual.jsonl'
 with actual.open('w') as f:
  for d,c,e,tr in itertools.zip_longest(read_raw(out/'raw.txt',cases),cases,expected,traces):
   assert d is not None and c is not None and d['index']==len(rows),'case count/order mismatch'
   rows.append(compare_record(c,e,tr,d))
   f.write(json.dumps(dict(id=c['id'],state=d['state'],memory=d['memory'],events=d['events']),separators=(',',':'))+'\n')
 result=dict(status='PASS' if all(x['passed'] for x in rows) else 'FAIL',selected=len(rows),architectural_passed=sum(x['architectural_passed'] for x in rows),event_stream_passed=sum(x['event_stream_passed'] for x in rows),passed=sum(x['passed'] for x in rows),failed=sum(not x['passed'] for x in rows),excluded=len(skips),excluded_reasons=dict(collections.Counter(x['reason'] for x in skips)),by_coverage={cov:dict(total=sum(x['coverage']==cov for x in rows),passed=sum(x['coverage']==cov and x['passed'] for x in rows)) for cov in set(x['coverage'] for x in rows)},rows=rows)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
 for row in [r for r in rows if not r['passed']][:3]:print(json.dumps(dict(id=row['id'],errors=row['errors'][:3])))
 raise SystemExit(0 if result['status']=='PASS' else 1)
if __name__=='__main__':main()
