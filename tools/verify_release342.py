from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((r/'verification_result_v34_2.json').read_text());assert m['fresh_simulation_runs']==23 and m['com_cases']==5
assert not m['gowin_tested'] and not m['hardware_tested'] and not m['hardware_stage_C_resolved']
for key in ('source_sha256','test_source_sha256'):
 for name,h in m[key].items():assert sha(r/name)==h,name
log=(r/'test_results_com_v34_2.log').read_text()
assert log.count('TEST ')==log.count('PASS com34 ')==log.count('$finish called')==5 and 'FATAL' not in log
assert log.count('EZ80RAM: PASS')==2 and 'DST=010000 EXP=31 READ=30 RETRY=30 ABS=30 LEFT=0201' in log
log=(r/'test_results_wait_v34_2.log').read_text();assert log.count('TEST ')==log.count('PASS ')==18 and 'FATAL' not in log
log=(r/'test_results_wait_before_v34_2.log').read_text();assert log.count('EXPECTED FAILURE')==2 and log.count('CPU entered write T3 before RAM completion')==2
old=json.loads((r/'verification_result_v34_1.json').read_text())
for name,h in old['source_sha256'].items():
 if name!='fpga/src/ez80_memory_bridge.v':assert sha(r/name)==h,name
com=(r/'hardware_test/EZ80RAM.COM').read_bytes();info=json.loads((r/'hardware_test/EZ80RAM_v34.json').read_text())
assert len(com)==info['bytes']==1200 and hashlib.sha256(com).hexdigest()==info['sha256']
data=[]
for line in (r/'hardware_test/ez80ram_v34.asm').read_text().splitlines():
 if line.strip().startswith('DEFB '):data.extend(int(v.strip()[:-1],16) for v in line.split('DEFB ',1)[1].split(';',1)[0].split(','))
assert bytes(data)==com and bytes(int(v,16) for v in (r/'hardware_test/EZ80RAM.hex').read_text().split())==com
for name,h in json.loads((r/'original_t80_sha256.json').read_text()).items():assert sha(r/name)==h,name
projects=list((r/'fpga').rglob('*.gprj'));assert len(projects)==7
for p in projects:
 for x in ET.parse(p).findall('.//File'):
  if x.attrib.get('enable')=='1':assert (p.parent/x.attrib['path'].replace('\\','/')).is_file(),(p,x.attrib['path'])
assert 'PASS changed Verilog syntax' in (r/'test_results_top_syntax_v34_2.log').read_text()
print('PASS V34.2: 23 simulations; 2 old failures reproduced; CPU/controller unchanged; exact COM/ASM/HEX; 7 projects')
