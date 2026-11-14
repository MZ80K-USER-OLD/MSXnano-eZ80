from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent
baseline=json.loads((r/'doc/R11_3_FPGA_SHA256.json').read_text())
changed=[n for n,h in baseline.items() if hashlib.sha256((r/n).read_bytes()).hexdigest()!=h]
variant='A' if '.PREDECODED_MSX(0)' in (r/'fpga/top_ez80.v').read_text() else 'B'
expected=['fpga/top_ez80.v'] if variant=='A' else ['fpga/src/memory_ez80.v'];assert changed==expected,(variant,changed)
s=(r/'fpga/top_ez80.v').read_text();assert f'.PREDECODED_MSX({0 if variant=="A" else 1})' in s
m=(r/'fpga/src/ez80_memory_bridge.v').read_text();assert 'assign msx_mreq_n = cpu_mreq_n | extended_window;' in m and "extended_window ? 16'h0000 : cpu_addr[15:0]" in m
# The actual slot-register logic must be copied without editing into the monitor.
a=s.index('    //expanded slot 3');b=s.index('    // slots decoding',a);assert (r/'sim/secondary_slot_r11_4.vh').read_text()==s[a:b]
coms=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text());assert len(coms)==20
for n,h in coms.items():assert hashlib.sha256((r/'hardware_test'/n).read_bytes()).hexdigest()==h,n
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
j=dict(variant=variant,changed_FPGA_files=changed,preloaded_COM_count=20,preloaded_COM_unchanged=True,SDC_CST_GPRJ_unchanged=True,separate_MSX16_and_extended24_buses_maintained=True,MSX_address_clamped_and_MREQ_blocked_for_extended_access=True,actual_secondary_slot_RTL_monitored=True,project_references=len(refs),GOWIN_run=False,hardware_run=False)
(r/'verification_release_r11_4.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS one-variable '+variant+' release audit: '+str(changed))
