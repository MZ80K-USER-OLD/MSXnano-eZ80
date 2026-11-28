"""Compare an independently executed DUT JSONL stream against this suite."""
import argparse,json,itertools
from pathlib import Path
from validate import blocks
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('actual',help='JSONL {id,state,memory,events} from the DUT');p.add_argument('--output',default='dut_results.json');a=p.parse_args();passed=0;failures=[];seen=set()
 with open(a.actual) as fa,(ROOT/'cases.jsonl').open() as fc,(ROOT/'events.expected.jsonl').open() as ft:
  for expected,case,trace,actual in itertools.zip_longest(blocks(ROOT/'tests.expected'),fc,ft,fa):
   if None in (expected,case,trace,actual):failures.append({'id':'stream','errors':['case counts differ']});break
   c=json.loads(case);t=json.loads(trace);d=json.loads(actual);errors=[]
   if d.get('id')!=c['id'] or c['id'] in seen:errors.append('case id/order mismatch or duplicate')
   seen.add(c['id'])
   for k,v in expected['state'].items():
    mask=c['mask'].get(k,0xffffff)
    if k not in d.get('state',{}):errors.append(f'missing state {k}')
    elif (d['state'][k]^v)&mask:errors.append(f'{k}: got {d["state"][k]:x} expected {v:x} mask {mask:x}')
   for addr,v in expected['memory'].items():
    if d.get('memory',{}).get(addr)!=v:errors.append('memory '+addr)
   if d.get('events')!=t['events']:errors.append('functional memory/I/O event stream differs')
   if errors:failures.append(dict(id=c['id'],errors=errors))
   else:passed+=1
 r=dict(status='PASS' if not failures else 'FAIL',passed=passed,failed=len(failures),failures=failures)
 Path(a.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='failures'}));raise SystemExit(bool(failures))
if __name__=='__main__':main()
