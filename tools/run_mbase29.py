"""Focused v29 cases; all are included in the main v29 plan."""
from pathlib import Path
from contextlib import redirect_stdout
import io,json,os
from parallel_matrix import run_matrix
r=Path(__file__).resolve().parent.parent
plan=json.loads((r/'tools/regression_cases_v29.json').read_text())
stream=io.StringIO();total=0
with redirect_stdout(stream):
 for entity in ('tb_mbase_absolute29','tb_mbase_control29','tb_isa_slots29','tb_mbase_bus29'):
  cases=[x['case'] for x in plan if x['entity']==entity]
  total+=run_matrix(r,entity,cases,'PASS',work_name='verification_mbase29')
assert total==7272
s=stream.getvalue();assert s.count('simulation stopped')==total
f=r/'test_results_mbase_focus_v29.log';tmp=f.with_suffix('.tmp');tmp.write_text(s);os.replace(tmp,f)
print('PASS focused MBASE and ISA cases',total,flush=True)
