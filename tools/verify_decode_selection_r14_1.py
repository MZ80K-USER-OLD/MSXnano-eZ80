"""Temporary-tree checks only; does not switch the live FPGA source."""
from pathlib import Path
import tempfile,shutil,json,hashlib
from select_decode_r14_1 import ROOT,select
from compare_decode_reports_r14_1 import compare,parse_report
r=ROOT;m=json.loads((r/'doc/R14_1_DECODE_VARIANTS.json').read_text())
with tempfile.TemporaryDirectory() as td:
 q=Path(td)
 for n in ['doc/R14_1_DECODE_VARIANTS.json',m['active']]+[v['path'] for v in m['variants'].values()]:
  (q/n).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,q/n)
 for variant in ['baseline','matrix']:
  select(variant,q);assert (q/m['active']).read_bytes()==(r/m['variants'][variant]['path']).read_bytes()
 (q/m['active']).write_bytes(b'user edits')
 try:select('baseline',q)
 except RuntimeError:pass
 else:raise AssertionError('User edits were overwritten')
 assert (q/m['active']).read_bytes()==b'user edits'
 shutil.copyfile(r/m['active'],q/m['active'])
 b=q/'synthetic_baseline.txt';n=q/'synthetic_matrix.txt'
 b.write_text('Logic | 19000 / 20736 (92%)\n--LUT,ALU,ROM16 | 18065(16254 LUT, 1811 ALU, 0 ROM16)\n')
 n.write_text('Logic | 19001 / 20736 (92%)\n--LUT,ALU,ROM16 | 18066(16255 LUT, 1811 ALU, 0 ROM16)\n')
 j=compare(b,n,True,q);assert j['LUT_delta']==1 and j['reverted']
 assert (q/m['active']).read_bytes()==(r/m['variants']['baseline']['path']).read_bytes()
 select('matrix',q)
 n.write_text('LUT | 16253/20736\n');j=compare(b,n,True,q)
 assert j['LUT_delta']==-1 and not j['reverted']
 assert (q/m['active']).read_bytes()==(r/m['variants']['matrix']['path']).read_bytes()
 n.write_text('Logic | 19000 / 20736 (92%)\n')
 try:parse_report(n)
 except ValueError:pass
 else:raise AssertionError('Logic percentage substituted for LUT count')
 # Once restored, every FPGA file is identical to the R14 manifest.
 baseline=json.loads((r/'doc/R14_FPGA_SHA256.json').read_text())
 for name,h in baseline.items():
  p=r/m['variants']['baseline']['path'] if name==m['active'] else r/name
  assert hashlib.sha256(p.read_bytes()).hexdigest()==h,name
print('PASS variant selection, user-edit protection, synthetic LUT rollback and complete R14 restoration')
(r/'verification_decode_selection_r14_1.json').write_text(json.dumps(dict(passed=True,live_source_switched=False,synthetic_reports_only=True,PowerShell_execution_tested=False,full_FPGA_R14_restoration_verified=True),indent=2)+'\n')
