"""Verify v33 evidence without rerunning simulations or rewriting historical logs."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,xml.etree.ElementTree as ET,subprocess
r=Path(__file__).resolve().parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((r/'verification_result_v33.json').read_text())
assert m['fresh_simulation_runs']==30 and m['inherited_cpu_tests_rerun'] is False
assert m['gowin_tested'] is False and m['hardware_tested'] is False
s=(r/'test_results_memory_v33.log').read_text()
assert s.count('TEST ')==s.count('PASS ')==s.count('$finish called')==30
assert 'FATAL' not in s and 'ERROR' not in s
assert s.count('transactions=517')==16 and s.count('transactions=518')==1
assert s.count('PASS cpu_memory33')==8 and s.count('PASS memory_compat33')==4
assert 'PASS bridge33 10240' in s
for group in ('source_sha256','test_source_sha256'):
 for name,h in m[group].items():assert sha(r/name)==h,name
prior=json.loads((r/'verification_result_v32.json').read_text())
for name,h in prior['source_sha256'].items():assert sha(r/name)==h,name
for name,h in json.loads((r/'original_t80_sha256.json').read_text()).items():assert sha(r/name)==h,name
assert 'PASS changed Verilog syntax' in (r/'test_results_top_syntax_v33.log').read_text()
projects=[]
for p in (r/'fpga').rglob('*.gprj'):
 projects.append(str(p.relative_to(r)))
 for x in ET.parse(p).findall('.//File'):
  if x.attrib.get('enable')=='1':assert (p.parent/x.attrib['path'].replace('\\','/')).is_file(),(p,x.attrib['path'])
assert len(projects)==7
cpu_project=ET.parse(r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj')
paths={x.attrib['path'] for x in cpu_project.findall('.//File')}
assert '../src/ez80_memory_bridge.v' in paths and '../src/memory_ez80.v' in paths and '../src/memory.v' not in paths
assert 'parameter EZ80_EXTENDED = 0' in (r/'fpga/top_ez80.v').read_text()
assert not (r/'DOCM').exists() and (r/'doc/MSXnano_eZ80_Memory_Allocation_v2.md').is_file()
# Historical CPU checks are unchanged and can be checked independently.
p=subprocess.run(['python3','tools/verify_release32.py'],cwd=r,text=True,capture_output=True)
assert p.returncode==0,p.stdout+p.stderr
print('PASS v33: 30 fresh memory simulations; inherited v32 CPU hashes/evidence; original T80; 7 project references')
