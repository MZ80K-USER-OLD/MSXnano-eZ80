"""Verify current V34 evidence; inherited V33/V32 records remain historical."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((r/'verification_result_v34.json').read_text())
assert m['fresh_simulation_runs']==5 and m['actual_com_executed'] and not m['full_msx_dos_simulated']
assert not m['gowin_tested'] and not m['hardware_tested'] and not m['inherited_tests_rerun']
log=(r/'test_results_com_v34.log').read_text()
assert log.count('TEST ')==log.count('PASS com34 ')==log.count('$finish called')==5
assert log.count('EZ80RAM: PASS')==2 and log.count('EZ80RAM: FAIL stage 1')==1 and log.count('EZ80RAM: FAIL stage C')==1
assert log.count('EZ80RAM: UNSUPPORTED')==1 and 'FATAL' not in log
assert all(case['CPU_DIV']==16 for case in m['cases'])
for key in ('source_sha256','test_source_sha256'):
 for name,h in m[key].items():assert sha(r/name)==h,name
old=json.loads((r/'verification_result_v33.json').read_text())
for name,h in old['source_sha256'].items():
 if name!='fpga/top_ez80.v':assert sha(r/name)==h,name
for name,h in json.loads((r/'original_t80_sha256.json').read_text()).items():assert sha(r/name)==h,name
com=r/'hardware_test/EZ80RAM.COM';info=json.loads((r/'hardware_test/EZ80RAM_v34.json').read_text())
assert com.stat().st_size==info['bytes']==891 and sha(com)==info['sha256']
assert bytes(int(v,16) for v in (r/'hardware_test/EZ80RAM.hex').read_text().split())==com.read_bytes()
listing=(r/'hardware_test/ez80ram_v34.asm').read_text();result=[]
for line in listing.splitlines():
 if line.strip().startswith('DEFB '):result += [int(x.strip()[:-1],16) for x in line.split('DEFB ',1)[1].split(';',1)[0].split(',')]
assert bytes(result)==com.read_bytes()
guard=0x070000+info['labels']['MSX_GUARD']
assert all(not s['destination']<=guard<s['destination']+s['bytes'] for s in info['segments'])
assert [s['destination'] for s in info['segments']]==[0x010000,0x01fffe,0x020100]
projects=list((r/'fpga').rglob('*.gprj'));assert len(projects)==7
for p in projects:
 for x in ET.parse(p).findall('.//File'):
  if x.attrib.get('enable')=='1':assert (p.parent/x.attrib['path'].replace('\\','/')).is_file(),(p,x.attrib['path'])
assert 'parameter EZ80_EXTENDED = 1' in (r/'fpga/top_ez80.v').read_text()
assert '.RESET_ADL (0)' in (r/'fpga/top_ez80.v').read_text()
assert 'PASS changed Verilog syntax' in (r/'test_results_top_syntax_v34.log').read_text()
assert (r/'doc').is_dir() and not (r/'DOCM').exists()
print('PASS V34: 5 COM scenarios, exact COM/ASM/HEX identity, CPU/memory unchanged, original T80, 7 projects')
