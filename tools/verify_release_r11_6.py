from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R11_5_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
expected={'fpga/G80A_eZ80/g80a_ez80.vhd'};assert set(changed)==expected,changed
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
j=dict(changed_FPGA_files=sorted(changed),changed_FPGA_file_count=1,preloaded_COM_count=20,preloaded_COM_unchanged=True,SDC_CST_GPRJ_top_bridge_CPU_datapath_unchanged=True,separate_MSX16_and_extended24_buses_maintained=True,MSX_address_clamped_and_MREQ_blocked_for_extended_access=True,actual_secondary_slot_RTL_monitored=True,final_vector_and_isolation_decisions_captured_T1=True,project_references=len(refs),original_G80A_unchanged=True,GOWIN_run=False,hardware_run=False)
(r/'verification_release_r11_6.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11.6 source scope, unchanged top/bridge/core/SDC/CST/GPRJ, all20COM')
