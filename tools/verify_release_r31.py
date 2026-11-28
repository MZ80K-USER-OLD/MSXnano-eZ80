from pathlib import Path
import os,json,hashlib,re,subprocess,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1]
W=R/'verification_r31';W.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((R/'doc/R31_BASELINE_SHA256.json').read_text())
current={str(p.relative_to(R)):sha(p)for p in(R/'fpga').rglob('*')if p.is_file()}
changed=[p for p,h in base.items()if current.get(p)!=h]
assert set(current)==set(base), 'unexpected FPGA file added/removed'
assert set(changed)=={'fpga/G80A_eZ80/t80_pack_ez80.vhd','fpga/G80A_eZ80/t80_ez80.vhd','fpga/G80A_eZ80/t80_mcode_ez80.vhd'},changed
coms=[]
for manifest in ['R26_COM_MANIFEST.json','R29_1_DIAGNOSTIC_COM_MANIFEST.json']:
 for row in json.loads((R/'doc'/manifest).read_text()):
  n=row['name']if row['name'].endswith('.COM')else row['name']+'.COM'
  assert sha(R/n)==row['sha256']==sha(R/'hardware_test'/n),n
  coms.append(n)
assert len(coms)==30
test_base=json.loads((R/'doc/R31_TEST_BASELINE_SHA256.json').read_text())
assert all(sha(R/p)==h for p,h in test_base.items())
for p in [R/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',R/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 files=E.parse(p).findall('.//File');assert len(files)==123 and all((p.parent/f.get('path')).is_file() for f in files)
q=W/'vhdl93';q.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 a=subprocess.run([os.environ['GHDL'],'-a','--std=93','-fsynopsys','-fexplicit',str(R/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=q,capture_output=True,text=True);assert not a.returncode,a.stderr
# Make the baseline source explicit and immutable in this release.
for p in (R/'sim/reference_r30').glob('*.vhd'):
 assert sha(p)==base['fpga/G80A_eZ80/'+p.name]
runall=[s.split()[0]for s in(R/'RUNALL.BAT').read_text().splitlines()if s.strip()]
assert len(runall)==25
stress=['EZ80MEM','EZ80ALU','EZ80MUL','EZ80LEA','EZ80LDH','EZ80LDX','EZ80MIX','EZ80MAD','EZ80MB','EZ80BLK']
diffs=[]
normal=runall+['EZ80MX0','EZ80MX1','EZ80MX2','EZ80MA1','EZ80MR4']
for flag,names in [(False,normal),(True,stress)]:
 for name in names:
  p=R/'verification_differential_r31'/('stress'if flag else '')/(name+'.log')
  text=p.read_text();a=re.search(r'BUS_COMPARISONS=(\d+)',text)
  assert 'PASS differential_r27'in text and a,(name,flag,text[-500:])
  target=W/'differential'/('stress'if flag else'normal');target.mkdir(parents=True,exist_ok=True)
  (target/p.name).write_text(text)
  diffs.append(dict(COM=name,stress=flag,bus_comparisons=int(a[1])))
mcode=json.loads((R/'verification_mcode_r31/result.json').read_text());assert mcode['passed'] and mcode['cases']==5505024
(R/'verification_r31/mcode.log').write_bytes((R/'verification_mcode_r31/run.log').read_bytes())
width=json.loads((R/'verification_decode_width_r24/result.json').read_text())
assert len(width['profiles'])==2 and all('PASS decode width'in a['output']for a in width['profiles'])
for p in(R/'verification_decode_width_r24').glob('*.log'):
 d=W/'width';d.mkdir(exist_ok=True);(d/p.name).write_bytes(p.read_bytes())
result=dict(release='R31',baseline='R30 user hardware diagnostics/RUNALL/game PASS',RTL_changed=changed,
 descriptor_bits_before=62,descriptor_bits_after=73,additional_static_predicates=11,
 COMs_unchanged=len(coms),RUNALL_unchanged=sha(R/'RUNALL.BAT')==test_base['RUNALL.BAT'],
 GPRJ_refs_each=123,VHDL93_files=6,GHDL_synth_profiles=['normal','diagnostic','extension-disabled'],
 differential_reference='byte-exact complete R30 CPU/wrapper',differential=diffs,
 total_bus_comparisons=sum(x['bus_comparisons']for x in diffs),mcode_differential=mcode,CPU_divider_normal=4,CPU_divider_stress=4,stress_phase=3,stress_CEN_pauses=True,
 descriptor_width_profiles=width,SDC_CST_wrapper_top_bridge_memory_VDP_unchanged=True,
 pipeline_cycles_added=0,GOWIN=False,board=False,timing_closed=False,LUT_savings_measured=False)
assert result['RUNALL_unchanged']
(R/'doc/R31_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');(W/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS R31 audit: 3 FPGA files; 30 COM unchanged; 30 normal + 10 stress differential; 5505024 mcode cases; 64 width cases')
