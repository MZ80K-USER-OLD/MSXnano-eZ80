from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET,tempfile,shutil,subprocess,re
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R11_9_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/t80_ez80.vhd'};assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r11-10-replay-') as td:
 q=Path(td);(q/'tools').mkdir();(q/'fpga/G80A_eZ80').mkdir(parents=True)
 p=q/'fpga/G80A_eZ80/t80_ez80.vhd';p.write_bytes((r/'doc/r11_9_upper_baseline/t80_ez80.vhd.txt').read_bytes());assert sha(p)==baseline['fpga/G80A_eZ80/t80_ez80.vhd']
 shutil.copyfile(r/'tools/extend_upper_r11_10.py',q/'tools/extend_upper_r11_10.py');subprocess.run(['python3',str(q/'tools/extend_upper_r11_10.py')],check=True)
 assert p.read_bytes()==(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_bytes()
u=json.loads((r/'verification_upper_r11_10_result.json').read_text())
assert u['fresh_runs']==6 and u['expected_failure_runs']==2 and u['event_coverage_mask']==255 and u['exchange_coverage']>0
assert u['maximum_event_family_count']==1 and all(sha(r/n)==h for n,h in u['sha256'].items())
core=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
assert core.count('Write_Class<=Classify_Write(')==5 and len(re.findall(r'\bIR\s*<=',core))==5
j0=json.loads((r/'verification_write_r11_10_result.json').read_text())
assert j0['total_input_combinations']==8388608 and all(sha(r/n)==h for n,h in j0['sha256'].items())
sdj=json.loads((r/'verification_sd_r11_9_result.json').read_text());assert sdj['fresh_runs']==8 and sdj['expected_failure_runs']==2 and all(sha(r/n)==h for n,h in sdj['sha256'].items())
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
j=dict(changed_FPGA_files=sorted(changed),changed_FPGA_file_count=1,source_replay_files=1,Upper_ordinary_shared_port=True,Upper_same_capture_edge=True,Upper_event_coverage_mask=u['event_coverage_mask'],Upper_exchange_coverage=u['exchange_coverage'],CPU_baseline="R11.9",SD_read_number_captured_with_select=True,SD_writes_unchanged=True,Write_Class_updated_at_all_IR_assignments=True,decoder_differential_combinations=8388608,preloaded_COM_count=20,preloaded_COM_unchanged=True,SDC_CST_GPRJ_top_bridge_wrapper_and_SDRAM_unchanged=True,separate_MSX16_and_extended24_buses_maintained=True,MSX_address_clamped_and_MREQ_blocked_for_extended_access=True,actual_secondary_slot_RTL_monitored=True,final_vector_and_isolation_decisions_captured_T1=True,project_references=len(refs),original_G80A_unchanged=True,GOWIN_run=False,hardware_run=False)
(r/'verification_release_r11_10.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11.10 source scope, only core Upper write port changed; all20COM unchanged')
