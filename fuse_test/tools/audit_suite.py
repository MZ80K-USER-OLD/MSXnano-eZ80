from pathlib import Path
import json,itertools,collections,hashlib
from run_fuse import blocks,FIELDS,R
n=0;native=collections.Counter();coverage=collections.Counter();ids=set();alias=[]
for c,i,e,t in itertools.zip_longest((json.loads(l) for l in (R/'suite/cases.jsonl').open()),blocks(R/'suite/tests.in'),blocks(R/'suite/tests.expected'),(json.loads(l) for l in (R/'suite/events.expected.jsonl').open())):
 assert all(x is not None for x in [c,i,e,t]);assert c['id']==i['id']==e['id']==t['id'] and c['id'] not in ids
 ids.add(c['id']);assert c['initial']==i['state'] and c['memory']==i['memory']
 assert set(c['initial'])==set(FIELDS)
 mem=dict(c['memory'])
 s=c['initial'];codeaddr={((s['PC']+k)&0xffffff) if s['ADL'] else (s['MBASE']<<16)|((s['PC']+k)&65535) for k in range(len(c['code']))}
 for ev in t['events']:
  assert ev['kind'] in ['MR','MW','PR','PW'] and 0<=ev['value']<256
  assert 0<=ev['address']<(65536 if ev['kind'][0]=='P' else 16777216)
  if ev['kind']=='MW':mem[f'{ev["address"]:06x}']=ev['value']
  if ev['kind']=='MR' and ev['address'] in codeaddr:alias.append(dict(id=c['id'],address=ev['address']))
 assert mem==e['memory']
 if c['coverage']=='native':native[c['instruction']]+=1
 coverage[c['coverage']]+=1;n+=1
assert n==28290 and len(native)==883 and all(x==16 for x in native.values())
cat=json.loads((R/'suite/opcode_catalog.json').read_text());assert {x['key'] for x in cat}==set(native)
result=dict(status='PASS',cases=n,encoding_cells=len(native),native_cases_each=16,coverage=dict(coverage),functional_read_overlaps_code=alias,
 expected_data_unchanged=True,oracle_reexecution=False,independent_spec_checks_reexecuted=False,
 sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'suite').iterdir() if p.is_file()})
(R/'doc/SUITE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='sha256'},indent=2))
