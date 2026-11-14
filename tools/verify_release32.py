from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent.parent
plan=json.loads((r/'tools/regression_cases_v32.json').read_text());m=json.loads((r/'verification_result_v32.json').read_text())
assert len(plan)==m['passed']==25127
s=(r/'test_results_v32.log').read_text();assert s.count('simulation stopped')==25127 and 'PASS all 25127 regression cases' in s and '(assertion failure)' not in s
for name,count in [('native_absolute',168),('compat',32),('suffix',8),('size',6),('exchange_compat',4),('stack_compat',8),('phase_compat',8),('decimal',1984),('restart',192),('relative',1664)]:
 s=(r/f'test_results_{name}_v32.log').read_text();assert s.count('simulation stopped')==count,name;assert '(assertion failure)' not in s,name
for name,h in m['source_sha256'].items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h,name
for name,h in json.loads((r/'original_t80_sha256.json').read_text()).items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h,name
new=[x for x in plan if x['entity'] in ('tb_decimal32','tb_restart32','tb_relative32')];assert len(new)==3840
assert sum(256 if x['case'].get('BATCH') else 1 for x in new if x['entity']=='tb_decimal32')==18304
print('PASS v32 release: 25127 + 234 = 25361 executions; decimal vectors 18304; source identity verified')
