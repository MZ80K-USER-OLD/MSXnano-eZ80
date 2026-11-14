from pathlib import Path
import tempfile,shutil,subprocess,json,hashlib,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent;previous=r.parent/'cpu_restart_r10';p2=r.parent/'ez80_future_tests_P2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='ez80-r11-replay-') as td:
 q=Path(td);(q/'fpga').mkdir();(q/'doc').mkdir();shutil.copytree(r/'fpga/G80A',q/'fpga/G80A');shutil.copytree(r/'tools',q/'tools',ignore=shutil.ignore_patterns('__pycache__'))
 # The platform transformer also patches the unchanged top file.
 baseline_top=(r/'fpga/top_ez80.v').read_text().replace('.DIAGNOSTICS (EZ80_EXTENDED), // P2 service, inactive until explicit D8\n        ','',1)
 (q/'fpga/top_ez80.v').write_text(baseline_top)
 for script in ['rebuild_from_t80.py']+[f'extend_r{i}.py' for i in range(2,12)]+['extend_platform_r11.py']:
  p=subprocess.run(['python3',str(q/'tools'/script)],text=True,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
 hashes={p.name:sha(p) for p in (q/'fpga/G80A_eZ80').glob('*.vhd')}
 for n,h in hashes.items():assert sha(r/'fpga/G80A_eZ80'/n)==h,n
 assert (q/'fpga/top_ez80.v').read_bytes()==(r/'fpga/top_ez80.v').read_bytes()
(r/'verification_rebuild_r11.json').write_text(json.dumps(dict(reproduced_files=7,sha256=hashes),indent=2)+'\n')
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():assert sha(r/'fpga/G80A'/(n+'.vhd'))==h,n
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
baseline=json.loads((r/'doc/R10_BASELINE_SHA256.json').read_text())
changed=[n for n,h in baseline.items() if sha(r/n)!=h]
assert set(changed)=={'fpga/top_ez80.v'}|{'fpga/G80A_eZ80/'+n for n in ('t80_ez80.vhd','t80_pack_ez80.vhd','t80_mcode_ez80.vhd','g80a_ez80.vhd')},changed
p2hash=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text())
for n,h in p2hash.items():
 p=r/'hardware_test'/n;assert sha(p)==h,n
 assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes(),n
 asm=[]
 for line in p.with_suffix('.asm').read_text().splitlines():
  line=line.split(';',1)[0].strip()
  if line.upper().startswith('DEFB '):asm.extend(int(x.strip()[:-1],16) for x in line[5:].split(','))
 assert bytes(asm)==p.read_bytes(),n+' assembly'
j=dict(changed_FPGA_files=changed,project_references=len(refs),all_project_files_exist=True,original_G80A_unchanged=True,bridge_SDRAM_constraints_GPRJ_unchanged=True,preloaded_P2_COM_unchanged=True,P2_SHA256=p2hash,GOWIN_run=False)
(r/'verification_release_r11.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11 replay7, project122 refs, original CPU, constraints/SDRAM/bridge unchanged, all COM identities')
