"""Print addresses / expected / actual values for one executed FUSE case."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2:raise SystemExit('Usage: python3 tools/show_case.py CASE_ID')
key=sys.argv[1];row=None
for batch in ['full_r37','events_r37']:
 data=json.loads((R/'results'/batch/'result.json').read_text())
 row=next((r for r in data['rows'] if r['id']==key),None)
 if row:break
if not row:
 skips=json.loads((R/'results/full_r37/excluded.json').read_text());s=next((x for x in skips if x['id']==key),None)
 raise SystemExit('NOT RUN: '+json.dumps(s) if s else 'CASE NOT FOUND')
def h(v,n):return 'UNKNOWN' if v is None else f'{v:0{n}X}'
print(key, 'PASS' if row['passed'] else 'UNMATCHED')
for e in row['errors']:
 if e['kind']=='memory':print(f'ADDR={e["address"].upper()} EXP={h(e["expected"],2)} ACT={h(e["actual"],2)}')
 elif e['kind']=='register':print(f'REG={e["register"]} EXP={h(e["expected"],6)} ACT={h(e["actual"],6)} MASK={h(e["mask"],6)}')
 elif e['kind']=='events':
  for tag in ['expected','actual']:
   ev=e[tag]
   print('EVENT '+tag.upper()+': '+('NONE' if ev is None else f'{ev["kind"]} ADDR={h(ev["address"],4 if ev["kind"].startswith("P") else 6)} VALUE={h(ev["value"],2)}'))
 else:print(json.dumps(e))
