from pathlib import Path
import tempfile,subprocess,shutil,hashlib,json,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R11_2_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/t80_ez80.vhd','fpga/G80A_eZ80/g80a_ez80.vhd','fpga/src/ez80_memory_bridge.v','fpga/src/memory_ez80.v','fpga/top_ez80.v'}
assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r11-3-replay-') as td:
 q=Path(td);(q/'tools').mkdir()
 for n in expected:
  p=q/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((r/'doc/r11_2_timing_baseline'/(n+'.txt')).read_bytes());assert sha(p)==baseline[n]
 p=q/'tools/extend_timing_r11_3.py';shutil.copyfile(r/'tools/extend_timing_r11_3.py',p);subprocess.run(['python3',str(p)],check=True)
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
# All constraints, GPRJ, pin assignments and original top are byte-identical.
for n in ['fpga/tang20k.sdc','fpga/tang20k.cst','fpga/top.v','fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj']:
 assert sha(r/n)==baseline[n],n
s=(r/'fpga/top_ez80.v').read_text();assert '.PREDECODED_MSX(1)' in s and '.A_MSX     (cpu_msx_addr)' in s and '.cpu_msx_addr(cpu_msx_addr)' in s
j=dict(changed_FPGA_files=sorted(changed),replay_files=5,project_references=len(refs),original_G80A_unchanged=True,CST_GPRJ_SDC_unchanged=True,preloaded_COM_count=20,preloaded_COM_unchanged=True,no_new_or_relaxed_timing_exceptions=True,registered_MSX_path_enabled_in_top=True,GOWIN_run=False)
(r/'verification_release_r11_3.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11.3 replay5, original CPU, project refs, all20COM, identical SDC')
