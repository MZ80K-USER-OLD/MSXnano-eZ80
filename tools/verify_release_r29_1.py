from pathlib import Path
import hashlib,json,subprocess,os,xml.etree.ElementTree as E,shutil
r=Path(__file__).resolve().parents[1];w=r/'verification_r29_1';w.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((r/'doc/R29_BASELINE_SHA256.json').read_text())
assert len(base)==245 and all(sha(r/p)==h for p,h in base.items())
assert len(list(p for p in(r/'fpga').rglob('*')if p.is_file()))==245
for p in[r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',r/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 files=E.parse(p).findall('.//File');assert len(files)==123 and all((p.parent/f.get('path')).is_file()for f in files)
q=w/'vhdl93';q.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 p=subprocess.run([os.environ['GHDL'],'-a','--std=93','-fsynopsys','-fexplicit',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=q,capture_output=True,text=True);assert not p.returncode,p.stderr
for row in json.loads((r/'doc/R26_COM_MANIFEST.json').read_text()):
 assert sha(r/row['name'])==row['sha256'] and sha(r/'hardware_test'/row['name'])==row['sha256']
for row in json.loads((r/'doc/R29_1_DIAGNOSTIC_COM_MANIFEST.json').read_text()):
 n=row['name']+'.COM';assert sha(r/n)==row['sha256'] and sha(r/'hardware_test'/n)==row['sha256']
 assert sha(r/'hardware_test'/(row['source']+'.COM'))==row['source_sha256']
a=json.loads((r/'verification_recovery_r29_1/result.json').read_text());b=json.loads((r/'verification_bad_tag_r29_1/result.json').read_text())
assert len(a['tests'])==10 and all(t['passed']for t in a['tests'])
assert len(b['tests'])==2 and all(t['passed']for t in b['tests'])
for d in ['verification_recovery_r29_1','verification_bad_tag_r29_1']:
 target=w/d;target.mkdir(exist_ok=True)
 for p in (r/d).iterdir():
  if p.suffix in ['.json','.log']:shutil.copy2(p,target/p.name)
result=dict(release='R29.1 recovery/diagnostic',FPGA_all_files_identical_to_R28=245,GPRJ_refs_each=123,VHDL93_files=6,existing_COMs_unchanged=26,new_diagnostic_COMs=4,fresh_targeted_runs=a['tests'],injected_bad_tag_runs=b['tests'],board_cause_proven=False,full_RUNALL_freshly_rerun=False,reference_R28_regression='prior release results; unchanged RTL',GOWIN_run=False,hardware_recovery_confirmed=False,timing_closed=False)
(r/'doc/R29_1_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');(w/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
(r/'R29_1_BUILD_ID.txt').write_text('R29.1 recovery/diagnostic\nFPGA all 245 files byte-identical to R28\nNew probes: EZ80MX0 / EZ80MX1 / EZ80MX2 / EZ80MA1\nGOWIN/board recovery pending\n')
print('PASS R29.1: all 245 FPGA files exact R28; original 26 COM unchanged; 4 probes; 10 targeted + 2 modeled fault runs')
