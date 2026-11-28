from pathlib import Path
import json,hashlib,re,os,subprocess,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];W=R/'verification_scope_r37';W.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((R/'doc/R37_BASELINE_R36_SHA256.json').read_text());current={str(p.relative_to(R)):sha(p) for p in (R/'fpga').rglob('*') if p.is_file()}
assert set(base)==set(current)
changed=[p for p in base if base[p]!=current[p]];assert changed==['fpga/G80A_eZ80/t80_ez80.vhd'],changed
old=(R/'sim/reference_r36/t80_ez80.vhd').read_text();new=(R/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
a=old.index('                    when "00" =>\n                        ACC <= I;');b=old.index('                    when "10" =>',a)
c=new.index('                    when "00" | "01" =>');d=new.index('                    when "10" =>',c)
restored=new[:c]+old[a:b]+new[d:];restored=restored.replace('        variable IR_Load_Byte : std_logic_vector(7 downto 0);\n','');assert restored==old,'change outside LD A,I/R byte/flags block'
for p in (R/'sim/reference_r36').glob('*.vhd'):assert sha(p)==base['fpga/G80A_eZ80/'+p.name]
assert len(list((R/'sim/reference_r36').glob('*.vhd')))==6
coms=[]
for manifest in ['R26_COM_MANIFEST.json','R29_1_DIAGNOSTIC_COM_MANIFEST.json']:
 for row in json.loads((R/'doc'/manifest).read_text()):
  n=row['name'] if row['name'].endswith('.COM') else row['name']+'.COM';assert sha(R/n)==row['sha256']==sha(R/'hardware_test'/n);coms.append(n)
assert len(set(coms))==len(coms)==30
assert all(sha(R/p)==h for p,h in json.loads((R/'doc/R32_TEST_BASELINE_SHA256.json').read_text()).items())
for p in [R/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',R/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 refs=E.parse(p).findall('.//File');assert len(refs)==123 and all((p.parent/f.get('path')).is_file() for f in refs)
w=W/'vhdl93';w.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 z=subprocess.run([os.environ['GHDL'],'-a','--std=93','-fsynopsys','-fexplicit',str(R/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=w,capture_output=True,text=True);assert not z.returncode,z.stderr
assert json.loads((R/'verification/r37_rtl_sha256.json').read_text())=={str(p.relative_to(R)):sha(p) for p in (R/'fpga/G80A_eZ80').glob('*.vhd')}
assert json.loads((R/'fuse_test/doc/R37_RTL_SHA256.json').read_text())=={p.name:sha(p) for p in (R/'fpga/G80A_eZ80').glob('*.vhd')}
def norm(p):return re.sub(r'\s+','',re.sub(r'/\*.*?\*/|//[^\n]*','',p.read_text(),flags=re.S))
assert norm(R/'verification/cpu_1.v')==norm(R/'fuse_test/build/dut.v')
(R/'verification_scope_r37/result.json').write_text(json.dumps(dict(RTL_changed=changed,FPGA_files=len(current),FPGA_sha256=current,COMs_unchanged=30,RUNALL_unchanged=True,GPRJ_refs_each=123,VHDL93=True,only_byte_selection_and_flags_for_LD_A_I_R=True,decoder_wrapper_memory_constraints_unchanged=True,FUSE_and_COM_models_identical=True),indent=2)+'\n')
print('PASS R37 scope: only LD A,I/R flags; 30 COM unchanged; VHDL93; FUSE/COM model identity')
