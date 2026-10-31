"""Validate complete logs and source hashes for the v30 release."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent.parent
plan=json.loads((r/'tools/regression_cases_v30.json').read_text());m=json.loads((r/'verification_result_v30.json').read_text())
assert len(plan)==m['passed']==16907
s=(r/'test_results_v30.log').read_text();assert s.count('simulation stopped')==16907 and 'PASS all 16907 regression cases' in s and '(assertion failure)' not in s
for name,count in [('native_absolute',168),('compat',32),('suffix',8),('size',6),('exchange_compat',4),('exchange_sp',2368)]:
 s=(r/f'test_results_{name}_v30.log').read_text();assert s.count('simulation stopped')==count,name;assert '(assertion failure)' not in s,name
for name,h in m['source_sha256'].items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h,name
for name,h in json.loads((r/'original_t80_sha256.json').read_text()).items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h,name
print('PASS v30 release: 16907 + 218 = 17125; CPU hashes and original T80 verified')
