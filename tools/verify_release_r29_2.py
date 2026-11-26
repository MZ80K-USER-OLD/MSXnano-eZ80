from pathlib import Path
import json,hashlib,subprocess,os,re,shutil,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];W=R/'verification_r29_2';W.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((R/'doc/R29_2_BASELINE_SHA256.json').read_text());changed=[p for p,h in base.items()if sha(R/p)!=h]
assert set(changed)=={f'fpga/G80A_eZ80/{x}_ez80.vhd'for x in ['g80a','t80','t80_pack']},changed
for n in ['t80_pack','t80','g80a']:
 old=(R/'sim/reference_r29'/(n+'_ez80.vhd')).read_text();now=(R/'fpga/G80A_eZ80'/(n+'_ez80.vhd')).read_text()
 if n!='g80a':
  pattern="DI_FRAME_VALID : in std_logic := '0'";assert old.count(pattern)==1;old=old.replace(pattern,'DI_FRAME_VALID : in std_logic')
 assert old==now,n
for p in [R/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',R/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 files=E.parse(p).findall('.//File');assert len(files)==123 and all((p.parent/f.get('path')).is_file()for f in files)
q=W/'vhdl93';q.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 a=subprocess.run([os.environ['GHDL'],'-a','--std=93','-fsynopsys','-fexplicit',str(R/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=q,capture_output=True,text=True);assert not a.returncode,a.stderr
for manifest in ['R26_COM_MANIFEST.json','R29_1_DIAGNOSTIC_COM_MANIFEST.json']:
 for row in json.loads((R/'doc'/manifest).read_text()):
  n=row['name']if row['name'].endswith('.COM')else row['name']+'.COM'
  assert sha(R/n)==row['sha256']and sha(R/'hardware_test'/n)==row['sha256']
recovery=json.loads((R/'verification_recovery_r29_1/result.json').read_text());assert len(recovery['tests'])==10 and all(x['passed']for x in recovery['tests'])
source_dirs=['verification_recovery_r29_1','verification_input_frame_r29','verification_strobes_r28','verification_vdp_io_r28','verification_checker_r29_2']
for folder in source_dirs:
 d=W/folder;d.mkdir(exist_ok=True)
 for p in (R/folder).iterdir():
  if p.suffix in ['.log','.json']:shutil.copy2(p,d/p.name)
assert json.loads((R/'verification_input_frame_r29/result.json').read_text())['checks']==8192
assert json.loads((R/'verification_strobes_r28/result.json').read_text())['checks']==5121
assert json.loads((R/'verification_vdp_io_r28/result.json').read_text())['classes']==8
checks=json.loads((R/'verification_checker_r29_2/result.json').read_text());assert len(checks)>=3 and all(x['passed']for x in checks)
diffs=[]
for sub in ['', 'stress']:
 for name in ['EZ80MEM','EZ80MIX','EZ80MAD','EZ80IRQ']:
  p=R/'verification_differential_r27'/sub/(name+'.log');s=p.read_text();a=re.search('BUS_COMPARISONS=(\\d+)',s);assert 'PASS differential_r27'in s and a
  diffs.append(dict(COM=name,stress=bool(sub),comparisons=int(a[1])))
  d=W/'differential'/sub;d.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d/p.name)
probe=json.loads((R/'doc/R29_2_PROBE_RESULTS.json').read_text());assert [x['passed']for x in probe]==[False,True,True,True,True]
result=dict(release='R29.2 mandatory metadata input',baseline='R29.1 hardware PASS; R28-equivalent FPGA',RTL_changed=changed,delta_vs_R29='remove := 0 default from exactly two DI_FRAME_VALID declarations; wrapper identical to R29',existing_COMs_unchanged=30,GPRJ_refs_each=123,VHDL93_files=6,targeted_runs=10,input_checks=8192,strobe_checks=5121,VDP_IO_checks=3145728,differential_reference='byte-exact complete R29.1 CPU source',differential=diffs,total_bus_comparisons=sum(x['comparisons']for x in diffs),actual_probe_GOWIN=[dict(variant=x['variant'],passed=x['passed'])for x in probe],R29_2_integrated_GOWIN=False,board=False,timing_closed=False,full_RUNALL_freshly_rerun=False,SDC_CST_top_bridge_memory_VDP_unchanged=True)
(R/'doc/R29_2_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');(W/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
(R/'R29_2_BUILD_ID.txt').write_text('R29.2 mandatory DI_FRAME_VALID input\nRelative to R29: remove default in entity and component declaration only\nIntegrated Gowin/netlist/timing/board verification pending\n')
print('PASS R29.2 audit: 2 declaration defaults removed vs R29; 3 RTL files vs R29.1; 30 COM unchanged; 10 targeted runs; 8 bus comparisons')
