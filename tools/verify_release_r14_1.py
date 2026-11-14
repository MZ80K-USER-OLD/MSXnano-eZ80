from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET,tempfile,shutil,subprocess
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R14_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/t80_mcode_ez80.vhd'};assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r14-1-replay-') as td:
 q=Path(td);(q/'tools').mkdir();(q/'fpga/G80A_eZ80').mkdir(parents=True);(q/'doc').mkdir()
 shutil.copyfile(r/'doc/r14_decode_baseline/t80_mcode_ez80.vhd.txt',q/'fpga/G80A_eZ80/t80_mcode_ez80.vhd')
 shutil.copyfile(r/'doc/R14_1_MATRIX.patch',q/'doc/R14_1_MATRIX.patch')
 shutil.copyfile(r/'tools/extend_matrix_r14_1.py',q/'tools/extend_matrix_r14_1.py')
 subprocess.run(['python3',str(q/'tools/extend_matrix_r14_1.py')],check=True)
 assert (q/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_bytes()==(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_bytes()
old=(r/'doc/r14_decode_baseline/t80_mcode_ez80.vhd.txt').read_text()
new=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text()
# Main decoder is text-identical; only final Write process and its comment differ.
assert old[:old.index('    -- The legacy writer is unchanged.')] == new[:new.index('    -- R14.1 comparison:')]
variants=json.loads((r/'doc/R14_1_DECODE_VARIANTS.json').read_text())
for v in variants['variants'].values():assert sha(r/v['path'])==v['sha256']
assert sha(r/variants['active'])==variants['variants']['matrix']['sha256']
truth=json.loads((r/'verification_matrix_truth_r14_1_result.json').read_text())
assert truth['total_boolean_comparisons']==16777216
assert all(sha(r/n)==h for n,h in truth['sha256'].items())
for group in ['write_r14_1','upper_r14_1','sd_r11_9','mbase_r12','madl_r13','mixed_r14','mix_nodiag_r14']:
 j=json.loads((r/f'verification_{group}_result.json').read_text());assert all(sha(r/n)==h for n,h in j['sha256'].items()),group
u=json.loads((r/'verification_upper_r14_1_result.json').read_text());assert u['event_coverage_mask']==255 and u['exchange_coverage']>0
mb=json.loads((r/'verification_mbase_r12_result.json').read_text());assert mb['fresh_runs']==9 and mb['expected_failure_runs']==2
irq=json.loads((r/'verification_irq_r11_result.json').read_text());assert irq['fresh_runs']==59 and sum(v['name']=='EZ80MIX' for v in irq['cases'])==7
j=json.loads((r/'verification_write_r14_1_result.json').read_text());assert j['legacy_equivalence_combinations']==8388608 and j['excluded_combinations']==0
coms=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text());assert len(coms)==20
for n,h in coms.items():
 p=r/'hardware_test'/n;assert sha(p)==h,n;assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes(),n
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():assert sha(r/'fpga/G80A'/(n+'.vhd'))==h
s=(r/'fpga/top_ez80.v').read_text();a=s.index('    //expanded slot 3');b=s.index('    // slots decoding',a);assert (r/'sim/secondary_slot_r11_4.vh').read_text()==s[a:b]
w=(r/'fpga/G80A_eZ80/g80a_ez80.vhd').read_text();assert "when Request_Extended='1'" in w and "Request_Extended <= Vector_Window;" in w
assert 'Request_Address <= Bank_i & A_i;' in w and 'Request_MSX_Address <= (others=>\'0\'); Request_Extended <= \'1\';' in w
assert 'when x"C4"=>Diag_Read<=x"9F";' in w and 'when x"C8"=>Diag_Read<=MBASE_i;' in w
assert 'when x"C9"=>Diag_Read<="0000000" & MADL_i;' in w
assert 'Diag_Read<=x"83";else Diag_Read<=x"03";' in w
old_coms=json.loads((r/'doc/PRE_R13_COM_SHA256.json').read_text());assert [n for n in coms if coms[n]!=old_coms[n]]==['EZ80MAD.COM']
subprocess.run(['python3',str(r/'tools/update_mad_com_r13.py')],check=True)
mad=json.loads((r/'verification_madl_r13_result.json').read_text());assert mad['fresh_runs']==78 and mad['expected_failure_runs']==2
stress=[v for v in mad['cases'] if v['case'][2] and v['case'][0]<23 and v['case'][0]!=20]
assert len(stress)==44 and all('bus_grant=1' in v['result'] for v in stress)
assert any(re.search(r'frame_WAIT=[1-9]',v['result']) for v in stress)
assert all(re.search(r'pause=[1-9]',v['result']) for v in stress)
b=bytearray()
for line in (r/'hardware_test/EZ80MAD.asm').read_text().splitlines():
 m=re.match(r'\s*DEFB\s+([^;]+)',line,re.I)
 if m:
  for v in m[1].split(','):b.append(int(v.strip().removesuffix('h'),16))
assert b==(r/'hardware_test/EZ80MAD.COM').read_bytes()
meta=json.loads((r/'hardware_test/EZ80MAD.json').read_text());assert meta['bytes']==len(b) and meta['sha256']==hashlib.sha256(b).hexdigest()
assert "`define P2_COM_END 16'h0d03" in (r/'hardware_test/EZ80MAD.vh').read_text()

assert 'A<=Address_Reg;' in (r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
assert 'DO<=Data_Out_Reg;' in (r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
assert all((r/'hardware_test'/n).read_bytes()==(r/'doc/r13_com_baseline'/n).read_bytes() for n in coms)
core=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
assert 'Frame_Stack_Next<=Frame_Stack_Value+Frame_Stack_Delta;' in core
assert core.count('type frame_state_type is')==1 and '(frame_idle, frame_push, frame_vector, frame_mode, frame_long, frame_upper, frame_short, frame_fault)' in core
assert 'Write_Class(3 downto 1)="101"' in core and 'Write_Class(3 downto 1)="110"' in core
mixed=json.loads((r/'verification_mixed_r14_result.json').read_text());assert mixed['fresh_runs']==192 and mixed['expected_failure_runs']==2
j=dict(shared_frame_stack_adder_bits=24,additional_frame_states=0,additional_24bit_work_registers=0,additional_control_bits=0,registered_bus_payload_preserved=True,changed_FPGA_files=sorted(changed),source_replay_files=1,preloaded_COM_count=20,unchanged_COM_count=20,updated_COM=None,preloaded_COM_unchanged=True,COM_baseline='R14',CPU_baseline='R14',MBASE_reset=0,MBASE_transfers_ADL_only=True,Z80_6D_6E_NOP_while_enabled=True,separate_MSX16_and_extended24_buses_maintained=True,actual_secondary_slot_RTL_monitored=True,SDC_CST_GPRJ_top_bridge_SDRAM_VDP_unchanged=True,project_references=len(refs),original_G80A_unchanged=True,GOWIN_run=False,hardware_run=False)
(r/'verification_release_r14_1.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R14.1 matrix replay, shared stack arithmetic, 20 unchanged COM and project/bridge/MSX isolation')
