from pathlib import Path
import json,copy,re,hashlib
from run_fuse import R,blocks
from compare import compare_record
wanted={'BASE_00_a0_native_s0','BASE_0A_a0_native_s0'};cases={};expected={};traces={};actual={};rows={}
for line in (R/'suite/cases.jsonl').open():
 d=json.loads(line)
 if d['id'] in wanted:cases[d['id']]=d
for d in blocks(R/'suite/tests.expected'):
 if d['id'] in wanted:expected[d['id']]=d
for line in (R/'suite/events.expected.jsonl').open():
 d=json.loads(line)
 if d['id'] in wanted:traces[d['id']]=d
res=json.loads((R/'results/full_r37/result.json').read_text());rows={d['id']:d for d in res['rows']}
for line in (R/'results/full_r37/dut_actual.jsonl').open():
 d=json.loads(line)
 if d['id'] in wanted:d.update(status=rows[d['id']]['status'],cycles=rows[d['id']]['cycles']);actual[d['id']]=d
checks=[]
def check(name,key,mutate,fail=True,kind=None):
 d=copy.deepcopy(actual[key]);mutate(d);x=compare_record(cases[key],expected[key],traces[key],d)
 assert x['passed']!=fail,(name,x)
 if kind:assert any(e['kind']==kind for e in x['errors']),name
 checks.append(dict(name=name,expected='FAIL' if fail else 'PASS',observed='PASS' if x['passed'] else 'FAIL'))
a='BASE_00_a0_native_s0';b='BASE_0A_a0_native_s0'
check('real NOP',a,lambda d:None,False)
check('real data read',b,lambda d:None,False)
check('Z flag bit flip',a,lambda d:d['state'].__setitem__('AF',d['state']['AF']^64),kind='register')
check('memory byte flip',a,lambda d:d['memory'].__setitem__(next(iter(d['memory'])),d['memory'][next(iter(d['memory']))]^1),kind='memory')
check('missing read event',b,lambda d:d['events'].clear(),kind='events')
check('wrong read byte',b,lambda d:d['events'][0].__setitem__('value',d['events'][0]['value']^1),kind='events')
check('timeout cannot PASS',a,lambda d:d.__setitem__('status',1),kind='TIMEOUT')
check('unknown PC cannot PASS',a,lambda d:d['state'].__setitem__('PC',None),kind='register')
check('provided undocumented flag mask',a,lambda d:d['state'].__setitem__('AF',d['state']['AF']^0x28),False)
# Build helper produced the same logic as the R37 model used for execution, ignoring source comments.
def norm(p):return re.sub(r'\s+','',re.sub(r'/\*.*?\*/|//[^\n]*','',p.read_text(),flags=re.S))
identity=hashlib.sha256(norm(R/'build/dut.v').encode()).hexdigest()
assert identity==(R/'doc/R37_MODEL_SEMANTIC_SHA256.txt').read_text().strip(),'generated model differs from the validated R37 model; review tool/version before claiming identical validation'
(R/'doc/COMPARATOR_CONTROLS_R37.json').write_text(json.dumps(dict(checks=checks,negative_controls=6,positive_controls=3,R37_model_semantic_sha256=identity),indent=2)+'\n')
print('PASS comparator: 6 negative and 3 positive controls; R37 model identity')
