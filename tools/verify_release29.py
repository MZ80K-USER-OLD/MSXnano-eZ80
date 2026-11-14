"""Verify complete v29 logs, case plan and untouched original T80 sources."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent.parent
plan=json.loads((r/'tools/regression_cases_v29.json').read_text())
meta=json.loads((r/'verification_result_v29.json').read_text())
assert len(plan)==meta['passed']==14539
log=(r/'test_results_v29.log').read_text();assert log.count('simulation stopped')==14539
assert 'PASS all 14539 regression cases' in log and '(assertion failure)' not in log
for name,count in [('native_absolute',168),('compat',32),('suffix',8),('size',6),('mbase_absolute',2016),('mbase_control',4860),('isa_slots',388),('mbase_bus',8),('mbase_irq',32)]:
 s=(r/f'test_results_{name}_v29.log').read_text()
 assert s.count('simulation stopped')==count,(name,s.count('simulation stopped'))
 assert '(assertion failure)' not in s,name
for name,h in meta['source_sha256'].items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h,name
for name,h in json.loads((r/'original_t80_sha256.json').read_text()).items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h,name
print('PASS release logs: 14539 + 168 + 32 + 8 + 6 = 14753; source identity verified')
