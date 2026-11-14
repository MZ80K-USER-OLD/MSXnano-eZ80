from pathlib import Path
import tempfile,subprocess,shutil,hashlib,json,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R11_1_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/t80_ez80.vhd','fpga/G80A_eZ80/t80_mcode_ez80.vhd','fpga/src/memory_ez80.v','fpga/tang20k.sdc'}
assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r11-2-replay-') as td:
 q=Path(td);(q/'tools').mkdir()
 for n in expected:
  p=q/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((r/'doc/r11_1_timing_baseline'/(n+'.txt')).read_bytes());assert sha(p)==baseline[n]
 for name in ['extend_timing_r11_2.py','extend_exsp_r11_2.py']:
  p=q/'tools'/name;shutil.copyfile(r/'tools'/name,p);subprocess.run(['python3',str(p)],check=True)
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
old=(r/'doc/r11_1_timing_baseline/fpga/tang20k.sdc.txt').read_text();new=(r/'fpga/tang20k.sdc').read_text()
def exc(s):return [x.strip() for x in s.splitlines() if x.strip().startswith(('set_false_path','set_multicycle_path','set_max_delay','set_min_delay','set_clock_latency'))]
assert exc(old)==exc(new)
j=dict(changed_FPGA_files=sorted(changed),replay_files=4,project_references=len(refs),original_G80A_unchanged=True,CST_GPRJ_top_wrapper_bridge_unchanged=True,SDRAM_receiver_capture_changed=True,preloaded_COM_count=20,preloaded_COM_unchanged=True,no_new_or_relaxed_timing_exceptions=True,CPU_ROM_logic_mapping_GOWIN_confirmation_required=True,GOWIN_run=False)
(r/'verification_release_r11_2.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11.2 replay4, original CPU, project refs, all20COM, unchanged timing exceptions')
