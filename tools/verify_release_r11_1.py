from pathlib import Path
import tempfile,subprocess,shutil,hashlib,json,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R11_FPGA_SHA256.json').read_text())
changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/'+n for n in ['t80_ez80.vhd','t80_pack_ez80.vhd','t80_mcode_ez80.vhd','g80a_ez80.vhd']}|{'fpga/src/ez80_memory_bridge.v','fpga/top_ez80.v','fpga/tang20k.sdc','fpga/tn_vdp_v3_v9958/src/clockdiv.v'}
assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r11-1-replay-') as td:
 q=Path(td);(q/'tools').mkdir()
 for n in expected:
  p=q/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((r/'doc/r11_timing_baseline'/(n+'.txt')).read_bytes());assert sha(p)==baseline[n]
 for script in ['extend_timing_r11_1.py','extend_condition_r11_1.py']:
  p=q/'tools'/script;shutil.copyfile(r/'tools'/script,p);subprocess.run(['python3',str(p)],check=True)
 for n in expected:assert (q/n).read_bytes()==(r/n).read_bytes(),n
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():assert sha(r/'fpga/G80A'/(n+'.vhd'))==h
coms=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text());assert len(coms)==20
for n,h in coms.items():
 p=r/'hardware_test'/n;assert sha(p)==h,n
 assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes(),n
 data=[]
 for line in p.with_suffix('.asm').read_text().splitlines():
  line=line.split(';',1)[0].strip()
  if line.upper().startswith('DEFB '):data.extend(int(x.strip()[:-1],16) for x in line[5:].split(','))
 assert bytes(data)==p.read_bytes(),n
j=dict(changed_FPGA_files=sorted(changed),replay_files=8,project_references=len(refs),original_G80A_unchanged=True,CST_GPRJ_SDRAM_controller_unchanged=True,preloaded_COM_count=20,preloaded_COM_unchanged=True,GOWIN_run=False)
(r/'verification_release_r11_1.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11.1 replay8, all project refs, original G80A, all20COM bytes')
