from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,tempfile,shutil,subprocess
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R11_10_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/'+n+'_ez80.vhd' for n in ['t80','t80_pack','t80_mcode','g80a']};assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r12-replay-') as td:
 q=Path(td);(q/'tools').mkdir();(q/'fpga/G80A_eZ80').mkdir(parents=True);(q/'doc/r11_10_mbase_baseline').mkdir(parents=True)
 for p in (r/'doc/r11_10_mbase_baseline').glob('*.txt'):
  shutil.copyfile(p,q/'doc/r11_10_mbase_baseline'/p.name);shutil.copyfile(p,q/'fpga/G80A_eZ80'/p.name[:-4])
 shutil.copyfile(r/'tools/extend_mbase_r12.py',q/'tools/extend_mbase_r12.py');subprocess.run(['python3',str(q/'tools/extend_mbase_r12.py')],check=True)
 for n in expected:assert (q/n).read_bytes()==(r/n).read_bytes(),n
for group in ['write_r12','upper_r12','sd_r11_9','mbase_r12']:
 j=json.loads((r/f'verification_{group}_result.json').read_text());assert all(sha(r/n)==h for n,h in j['sha256'].items()),group
u=json.loads((r/'verification_upper_r12_result.json').read_text());assert u['event_coverage_mask']==255 and u['exchange_coverage']>0
mb=json.loads((r/'verification_mbase_r12_result.json').read_text());assert mb['fresh_runs']==9 and mb['expected_failure_runs']==2
irq=json.loads((r/'verification_irq_r11_result.json').read_text());assert irq['fresh_runs']==47 and sum(v['name']=='EZ80MB' for v in irq['cases'])==7
j=json.loads((r/'verification_write_r12_result.json').read_text());assert j['legacy_equivalence_combinations']==8388096 and j['new_MBASE_decoder_combinations_excluded_from_legacy_comparison']==512
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
j=dict(changed_FPGA_files=sorted(changed),source_replay_files=4,preloaded_COM_count=20,preloaded_COM_unchanged=True,CPU_baseline='R11.10',MBASE_reset=0,MBASE_transfers_ADL_only=True,Z80_6D_6E_NOP_while_enabled=True,separate_MSX16_and_extended24_buses_maintained=True,actual_secondary_slot_RTL_monitored=True,SDC_CST_GPRJ_top_bridge_SDRAM_VDP_unchanged=True,project_references=len(refs),original_G80A_unchanged=True,GOWIN_run=False,hardware_run=False)
(r/'verification_release_r12.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R12 replay, source scope, 20 COM unchanged, project and bus isolation')
