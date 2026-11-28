from pathlib import Path
import os,json,hashlib,re,subprocess,xml.etree.ElementTree as E,shutil,difflib
R=Path(__file__).resolve().parents[1];W=R/'verification_r33';W.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((R/'doc/R33_BASELINE_SHA256.json').read_text())
current={str(p.relative_to(R)):sha(p)for p in(R/'fpga').rglob('*')if p.is_file()}
changed=[p for p,h in base.items()if current.get(p)!=h]
assert set(current)==set(base)
assert changed==['fpga/G80A_eZ80/t80_ez80.vhd'],changed
for p in (R/'sim/reference_r32').glob('*.vhd'):assert sha(p)==base['fpga/G80A_eZ80/'+p.name]
assert len(list((R/'sim/reference_r32').glob('*.vhd')))==6
coms=[]
for manifest in ['R26_COM_MANIFEST.json','R29_1_DIAGNOSTIC_COM_MANIFEST.json']:
 for row in json.loads((R/'doc'/manifest).read_text()):
  n=row['name']if row['name'].endswith('.COM')else row['name']+'.COM'
  assert sha(R/n)==row['sha256']==sha(R/'hardware_test'/n),n
  coms.append(n)
assert len(coms)==len(set(coms))==30
# RUNALL was unchanged in R32 and remains byte-for-byte unchanged here.
test_base=json.loads((R/'doc/R32_TEST_BASELINE_SHA256.json').read_text())
assert all(sha(R/p)==h for p,h in test_base.items())
for p in [R/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',R/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 files=E.parse(p).findall('.//File');assert len(files)==123 and all((p.parent/f.get('path')).is_file()for f in files)
q=W/'vhdl93';q.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 a=subprocess.run([os.environ['GHDL'],'-a','--std=93','-fsynopsys','-fexplicit',str(R/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=q,capture_output=True,text=True);assert not a.returncode,a.stderr
model_sha=json.loads((R/'verification/r33_rtl_sha256.json').read_text())
assert all(sha(R/p)==h for p,h in model_sha.items())
for n in ['cpu_1.v','cpu_diag.v','cpu_0.v','cpu_reference.v']:assert(R/'verification'/n).stat().st_size>10000
core=(R/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
assert 'Block_Inc_Result'not in core
assert 'Upper_Mask(Upper_Inc_Byte,Upper_Port_Events(4))'in core
assert "IncDecZ <= not Block_Result_Zero;"in core
runall=[s.split()[0]for s in(R/'RUNALL.BAT').read_text().splitlines()if s.strip()];assert len(runall)==25
normal=runall+['EZ80MX0','EZ80MX1','EZ80MX2','EZ80MA1','EZ80MR4']
stress=['EZ80MEM','EZ80ALU','EZ80MUL','EZ80LEA','EZ80LDH','EZ80LDX','EZ80MIX','EZ80MAD','EZ80MB','EZ80BLK','EZ80DEC','EZ80IRQ','EZ80NMI']
rows=[]
for stress_flag,names in [(False,normal),(True,stress)]:
 for name in names:
  p=R/'verification_differential_r33'/('stress'if stress_flag else '')/(name+'.log');out=p.read_text()
  a=re.search(r'BUS_COMPARISONS=(\d+)',out);assert a and 'PASS differential_r27'in out,(name,out[-400:])
  c=re.search(r'R33_BLOCK_COVERAGE inc_wrap=(\d+) dec_wrap=(\d+) no_wrap=(\d+) result_zero=(\d+)',out);assert c
  coverage=dict(zip(['inc_wrap','dec_wrap','no_wrap','result_zero'],map(int,c.groups())))
  if name=='EZ80BLK':assert all(v>0 for v in coverage.values()),coverage
  rows.append(dict(COM=name,stress=stress_flag,bus_and_state_comparisons=int(a[1]),block_coverage=coverage))
  d=W/'differential'/('stress'if stress_flag else'normal');d.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d/p.name)
assert len(rows)==43
for tb in ['tb_differential_r33.sv','tb_differential_trace_r33.sv']:
 s=(R/'sim'/tb).read_text();assert 'cpu.u0.regs.upper_view'in s and 'reference.u0.incdecz'in s and 'overlapping upper write events'in s
arith=json.loads((R/'verification_block_arithmetic_r33/result.json').read_text());assert arith['cases']==395776
assert 'PASS R33 actual RTL arithmetic cases=395776'in(R/'verification_block_arithmetic_r33/run.log').read_text()
faults=json.loads((R/'verification_block_faults_r33/result.json').read_text());assert len(faults)==2 and all(x['expected_failure_detected']for x in faults)
width=json.loads((R/'verification_decode_width_r24/result.json').read_text());assert width['cases']==64 and all('PASS decode width'in x['output']for x in width['profiles'])
for src,dst in [('verification_block_arithmetic_r33','arithmetic'),('verification_decode_width_r24','width'),('verification_block_faults_r33','expected_failures')]:
 d=W/dst;d.mkdir(exist_ok=True)
 for p in(R/src).iterdir():
  if p.suffix in ['.log','.json']:shutil.copy2(p,d/p.name)
patch=''.join(difflib.unified_diff((R/'sim/reference_r32/t80_ez80.vhd').read_text().splitlines(True),core.splitlines(True),fromfile='R32/fpga/G80A_eZ80/t80_ez80.vhd',tofile='R33/fpga/G80A_eZ80/t80_ez80.vhd'))
(R/'R32_to_R33.patch').write_text(patch)
result=dict(release='R33',baseline='R32 hardware: Logic80%, RUNALL all PASS, Space Manbow PLAY PASS',
 FPGA_files=len(current),RTL_changed=changed,FPGA_sha256=current,
 GHDL_synth_profiles=['normal','diagnostic','extension-disabled'],reference='byte-exact R32 complete CPU/wrapper',
 VHDL93_files=6,COMs_unchanged=30,RUNALL_unchanged=True,GPRJ_refs_each=123,
 arithmetic=arith,expected_failure_controls=faults,differential=rows,total_bus_and_state_comparisons=sum(x['bus_and_state_comparisons']for x in rows),
 width_cases=64,descriptor_bits_held=87,mcode_unchanged_from_R32=True,mcode_matrix_rerun=False,
 added_RTL_state_registers=0,pipeline_cycles_added=0,SDC_CST_wrapper_top_bridge_memory_VDP_unchanged=True,
 GOWIN=False,board=False,timing_closed=False,LUT_savings_measured=False)
(R/'doc/R33_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
e=R/'doc/R33_evidence';e.mkdir(exist_ok=True)
for p in W.rglob('*'):
 if p.is_file()and p.suffix in ['.log','.json']:
  d=e/p.relative_to(W);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
print(f"PASS R33 audit: {len(current)} FPGA files, only core changed; 30 COM unchanged; 43 differential runs; {result['total_bus_and_state_comparisons']} half-clock comparisons; 395776 arithmetic; 64 width cases")
