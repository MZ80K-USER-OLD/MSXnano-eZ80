"""R37 vs R36: original oracle unchanged; only ED57/5F should improve."""
from pathlib import Path
import json,csv,collections
R=Path(__file__).resolve().parents[1];rows=[];old_rows=[]
for newbatch,oldbatch in [('full_r37','full_r36'),('events_r37','events_r36')]:
 new=json.loads((R/'results'/newbatch/'result.json').read_text());old=json.loads((R/'baseline_r36'/oldbatch/'result.json').read_text())
 assert [r['id'] for r in new['rows']]==[r['id'] for r in old['rows']]
 for n,o in zip(new['rows'],old['rows']):
  if n['instruction'] not in ['ED_57','ED_5F']:assert n==o,('unrelated case changed',n['id'])
  else:assert n['passed'],n
  rows.append(n);old_rows.append(o)
assert len(rows)==27170
fixed=[n['id'] for n,o in zip(rows,old_rows) if n['passed'] and not o['passed']];regressed=[n['id'] for n,o in zip(rows,old_rows) if not n['passed'] and o['passed']]
assert len(fixed)==50 and not regressed
assert sum(r['instruction'] in ['ED_57','ED_5F'] for r in rows)==64
result=dict(release='R37',executed=len(rows),passed=sum(r['passed'] for r in rows),unmatched=sum(not r['passed'] for r in rows),not_run_policy=992,not_run_unimplemented=128,LD_A_I_R_passed=64,LD_A_I_R_total=64,newly_passed_vs_R36=len(fixed),new_failures_vs_R36=regressed,unrelated_cases_identical=27106,expected_changed=False,all_PASS=False,remaining_issues_unchanged=True)
assert result['passed']==25232 and result['unmatched']==1938
(R/'doc/R37_FUSE_SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
(R/'doc/R37_NEWLY_PASSING.json').write_text(json.dumps(fixed,indent=2)+'\n')
byid={r['id']:r for r in rows}
with (R/'baseline_r36/CASE_RESULTS.csv').open() as f:source=list(csv.DictReader(f))
for row in source:
 n=byid.get(row['id'])
 if n:
  row['strict_pass']=str(n['passed']);row['architectural_pass']=str(n['architectural_passed']);row['event_stream_pass']=str(n['event_stream_passed'])
  row['first_error']=json.dumps(n['errors'][0],separators=(',',':')) if n['errors'] else ''
  if n['instruction'] in ['ED_57','ED_5F']:row['category']='STRICT_PASS'
with (R/'doc/R37_CASE_RESULTS.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=source[0].keys());w.writeheader();w.writerows(source)
print(json.dumps(result,indent=2))
