from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
m=json.loads((r/'verification_result_v34_2.json').read_text());w=json.loads((r/'verification_wait_v34_2.json').read_text())
assert w['passed']==18 and w['expected_old_failures']==2
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in w['source_sha256'].items():assert sha(r/name)==h,name
m.update(fresh_simulation_runs=23,com_cases=5,write_wait_cases=16,bridge_cases=1,sdram_model_cases=1,
 expected_old_failure_reproductions=2,hardware_stage_C_resolved=False,
 change='WAIT asserts from extended MREQ before WR; copy-failure detail capture added')
m['test_source_sha256'].update(w['source_sha256'])
(r/'verification_result_v34_2.json').write_text(json.dumps(m,indent=2)+'\n')
print('Collected 23 current simulations; old failure reproductions excluded')
