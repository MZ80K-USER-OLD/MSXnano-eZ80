from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET,tempfile,shutil,subprocess
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R12_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/'+n+'_ez80.vhd' for n in ['t80','t80_pack','t80_mcode','g80a']};assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r13-replay-') as td:
 q=Path(td);(q/'tools').mkdir();(q/'fpga/G80A_eZ80').mkdir(parents=True);(q/'doc/r12_madl_baseline').mkdir(parents=True)
 for p in (r/'doc/r12_madl_baseline').glob('*.txt'):
  shutil.copyfile(p,q/'doc/r12_madl_baseline'/p.name);shutil.copyfile(p,q/'fpga/G80A_eZ80'/p.name[:-4])
 shutil.copyfile(r/'doc/R13_MADL.patch',q/'doc/R13_MADL.patch');shutil.copyfile(r/'tools/extend_madl_r13.py',q/'tools/extend_madl_r13.py');subprocess.run(['python3',str(q/'tools/extend_madl_r13.py')],check=True)
 for n in expected:assert (q/n).read_bytes()==(r/n).read_bytes(),n
for group in ['write_r13','upper_r13','sd_r11_9','mbase_r12','madl_r13']:
 j=json.loads((r/f'verification_{group}_result.json').read_text());assert all(sha(r/n)==h for n,h in j['sha256'].items()),group
u=json.loads((r/'verification_upper_r13_result.json').read_text());assert u['event_coverage_mask']==255 and u['exchange_coverage']>0
mb=json.loads((r/'verification_mbase_r12_result.json').read_text());assert mb['fresh_runs']==9 and mb['expected_failure_runs']==2
irq=json.loads((r/'verification_irq_r11_result.json').read_text());assert irq['fresh_runs']==53 and sum(v['name']=='EZ80MAD' for v in irq['cases'])==7
j=json.loads((r/'verification_write_r13_result.json').read_text());assert j['legacy_equivalence_combinations']==8388096 and j['new_MADL_decoder_combinations_excluded_from_legacy_comparison']==512
coms=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text());assert len(coms)==20
for n,h in coms.items():
 p=r/'hardware_test'/n;assert sha(p)==h,n;assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes(),n
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():assert sha(r/'fpga/G80A'/(n+'.vhd'))==h
s=(r/'fpga/top_ez80.v').read_text();a=s.index('    //expanded slot 3');b=s.index('    // slots decoding',a);assert (r/'sim/secondary_slot_r11_4.vh').read_text()==s[a:b]
w=(r/'fpga/G80A_eZ80/g80a_ez80.vhd').read_text();assert "when Request_Extended='1'" in w and "Request_Extended <= Vector_Window;" in w
assert 'Request_Address <= Bank_i & A_i;' in w and 'Request_MSX_Address <= (others=>\'0\'); Request_Extended <= \'1\';' in w
assert 'when x"C4"=>Diag_Read<=x"97";' in w and 'when x"C8"=>Diag_Read<=MBASE_i;' in w
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

j=dict(changed_FPGA_files=sorted(changed),source_replay_files=4,preloaded_COM_count=20,unchanged_COM_count=19,updated_COM='EZ80MAD.COM',preloaded_COM_unchanged=False,CPU_baseline='R12',MBASE_reset=0,MBASE_transfers_ADL_only=True,Z80_6D_6E_NOP_while_enabled=True,separate_MSX16_and_extended24_buses_maintained=True,actual_secondary_slot_RTL_monitored=True,SDC_CST_GPRJ_top_bridge_SDRAM_VDP_unchanged=True,project_references=len(refs),original_G80A_unchanged=True,GOWIN_run=False,hardware_run=False)
(r/'verification_release_r13.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R13 replay, 19 unchanged COM and MAD startup update, project and bus isolation')
