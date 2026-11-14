from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((r/'verification_result_v34_1.json').read_text());assert m['fresh_simulation_runs']==151 and m['com_cases']==5
assert not m['gowin_tested'] and not m['hardware_tested'] and not m['full_bios_boot_verified'] and not m['v34_black_screen_root_cause_confirmed']
for key in ('source_sha256','test_source_sha256'):
 for name,h in m[key].items():assert sha(r/name)==h,name
log=(r/'test_results_com_v34_1.log').read_text()
assert log.count('TEST ')==log.count('PASS com34 ')==log.count('$finish called')==5 and 'FATAL' not in log
assert log.count('EZ80RAM: PASS')==2 and 'EZ80RAM: FAIL stage 1' in log and 'EZ80RAM: FAIL stage C' in log and 'EZ80RAM: UNSUPPORTED' in log
log=(r/'test_results_guard_compat_v34_1.log').read_text();assert log.count('simulation stopped')==16 and '(assertion failure)' not in log
selected=json.loads((r/'verification_selected_v34_1.json').read_text());assert selected['passed']==selected['total']==129 and not selected['failed']
log=(r/'test_results_selected_v34_1.log').read_text();assert log.count('simulation stopped')==129 and '(assertion failure)' not in log
log=(r/'test_results_bios_guard_v34_1.log').read_text();assert 'PASS BIOS comparison interval' in log and '(assertion failure)' not in log
com=(r/'hardware_test/EZ80RAM.COM').read_bytes();info=json.loads((r/'hardware_test/EZ80RAM_v34.json').read_text())
assert len(com)==info['bytes']==931 and hashlib.sha256(com).hexdigest()==info['sha256']
listing=(r/'hardware_test/ez80ram_v34.asm').read_text();data=[]
for line in listing.splitlines():
 if line.strip().startswith('DEFB '):data.extend(int(v.strip()[:-1],16) for v in line.split('DEFB ',1)[1].split(';',1)[0].split(','))
assert bytes(data)==com
assert bytes(int(v,16) for v in (r/'hardware_test/EZ80RAM.hex').read_text().split())==com
for name,h in json.loads((r/'original_t80_sha256.json').read_text()).items():assert sha(r/name)==h,name
projects=list((r/'fpga').rglob('*.gprj'));assert len(projects)==7
for p in projects:
 for x in ET.parse(p).findall('.//File'):
  if x.attrib.get('enable')=='1':assert (p.parent/x.attrib['path'].replace('\\','/')).is_file(),(p,x.attrib['path'])
assert '.BOOT_Z80_COMPAT (EZ80_EXTENDED)' in (r/'fpga/top_ez80.v').read_text()
assert 'PASS changed Verilog syntax' in (r/'test_results_top_syntax_v34_1.log').read_text()
assert (r/'doc/SDRAM_Physical_Map_Implementation_v34_1.md').is_file()
print('PASS V34.1: 151 simulations, original T80, exact COM/ASM/HEX, 7 GPRJ references; physical map documented')
