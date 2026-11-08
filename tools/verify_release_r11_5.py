from pathlib import Path
import tempfile,subprocess,shutil,hashlib,json,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R11_4B_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/g80a_ez80.vhd','fpga/src/memory_ez80.v'};assert set(changed)==expected,changed
with tempfile.TemporaryDirectory(prefix='r11-5-replay-') as td:
 q=Path(td);(q/'tools').mkdir()
 for n in expected:
  p=q/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((r/'doc/r11_4B_baseline'/(n+'.txt')).read_bytes());assert sha(p)==baseline[n]
 p=q/'tools/extend_timing_r11_5.py';shutil.copyfile(r/'tools/extend_timing_r11_5.py',p);subprocess.run(['python3',str(p)],check=True)
 for n in expected:assert (q/n).read_bytes()==(r/n).read_bytes(),n
coms=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text());assert len(coms)==20
for n,h in coms.items():
 p=r/'hardware_test'/n;assert sha(p)==h,n;assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes(),n
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():assert sha(r/'fpga/G80A'/(n+'.vhd'))==h
w=(r/'fpga/G80A_eZ80/g80a_ez80.vhd').read_text();qual=w[w.index('    Vector_Window <='):w.index('    -- Only the refresh phase')]
assert "Write='0'" not in qual and 'Vector_Read_Request <= Request_Vector and not Request_Write;' in qual
assert 'Request_Vector <= Vector_Window' in w
assert '.PREDECODED_MSX(1)' in (r/'fpga/top_ez80.v').read_text()
s=(r/'fpga/top_ez80.v').read_text();a=s.index('    //expanded slot 3');b=s.index('    // slots decoding',a);assert (r/'sim/secondary_slot_r11_4.vh').read_text()==s[a:b]
j=dict(changed_FPGA_files=sorted(changed),source_replay_files=2,preloaded_COM_count=20,preloaded_COM_unchanged=True,SDC_CST_GPRJ_top_bridge_CPU_datapath_unchanged=True,separate_MSX16_and_extended24_buses_maintained=True,MSX_address_clamped_and_MREQ_blocked_for_extended_access=True,actual_secondary_slot_RTL_monitored=True,diagnostic_write_qualification_uses_captured_request=True,project_references=len(refs),original_G80A_unchanged=True,GOWIN_run=False,hardware_run=False)
(r/'verification_release_r11_5.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11.5 replay2, unchanged top/bridge/core/SDC/CST/GPRJ, all20COM')
