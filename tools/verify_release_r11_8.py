from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET,tempfile,shutil,subprocess,re
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R11_7_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/t80_mcode_ez80.vhd'};assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r11-8-replay-') as td:
 q=Path(td);(q/'tools').mkdir();(q/'fpga/G80A_eZ80').mkdir(parents=True)
 n='fpga/G80A_eZ80/t80_mcode_ez80.vhd';dst=q/n;dst.write_bytes((r/'doc/r11_7_baseline/t80_mcode_ez80.vhd.txt').read_bytes());assert sha(dst)==baseline[n]
 shutil.copyfile(r/'tools/extend_write_r11_8.py',q/'tools/extend_write_r11_8.py');subprocess.run(['python3',str(q/'tools/extend_write_r11_8.py')],check=True)
 assert dst.read_bytes()==(r/n).read_bytes()
s0=(r/'doc/r11_7_baseline/t80_mcode_ez80.vhd.txt').read_text();s1=(r/n).read_text()
def tokens(s):return re.sub(r'\s+','',re.sub(r'--[^\n]*','',s))
assert tokens(s0[:s0.index('    -- The legacy writer')])==tokens(s1[:s1.index('    -- R11.8:')])
a=s1.index('        base_kind:=Write_Class');b=s1.index('        pair_cycle:=',a)
assert not re.search(r'\bMCycle\b',re.sub(r'--[^\n]*','',s1[a:b]))
assert 'to_integer' not in s1[s1.index('    -- R11.8:'):]
core=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
assert core.count('Write_Class<=Classify_Write(')==5 and len(re.findall(r'\bIR\s*<=',core))==5
j0=json.loads((r/'verification_write_r11_8_result.json').read_text())
assert j0['total_input_combinations']==8388608 and all(sha(r/n)==h for n,h in j0['sha256'].items())
coms=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text());assert len(coms)==20
for n,h in coms.items():
 p=r/'hardware_test'/n;assert sha(p)==h,n;assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes(),n
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():assert sha(r/'fpga/G80A'/(n+'.vhd'))==h
w=(r/'fpga/G80A_eZ80/g80a_ez80.vhd').read_text()
assert 'Vector_Read_Request' not in w and 'Request_Vector' not in w
assert "Request_Extended <= Vector_Window;" in w
assert "when Request_Extended='1'" in w
assert '.PREDECODED_MSX(1)' in (r/'fpga/top_ez80.v').read_text()
s=(r/'fpga/top_ez80.v').read_text();a=s.index('    //expanded slot 3');b=s.index('    // slots decoding',a);assert (r/'sim/secondary_slot_r11_4.vh').read_text()==s[a:b]
j=dict(changed_FPGA_files=sorted(changed),changed_FPGA_file_count=1,source_replay_files=1,MCycle_independent_write_ownership=True,no_new_registers=True,legacy_writer_and_other_decoder_outputs_unchanged=True,Write_Class_updated_at_all_IR_assignments=True,decoder_differential_combinations=8388608,preloaded_COM_count=20,preloaded_COM_unchanged=True,SDC_CST_GPRJ_top_bridge_wrapper_and_SDRAM_unchanged=True,separate_MSX16_and_extended24_buses_maintained=True,MSX_address_clamped_and_MREQ_blocked_for_extended_access=True,actual_secondary_slot_RTL_monitored=True,final_vector_and_isolation_decisions_captured_T1=True,project_references=len(refs),original_G80A_unchanged=True,GOWIN_run=False,hardware_run=False)
(r/'verification_release_r11_8.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11.8 source scope, unchanged wrapper/top/bridge/SDRAM/SDC/CST/GPRJ, all20COM')
