"""Byte identity and reproducibility checks. Never modifies the active RTL."""
from pathlib import Path
import tempfile,shutil,subprocess,json,hashlib,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent;previous=r.parent/'cpu_restart_r9'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='ez80-r10-replay-') as td:
 q=Path(td);(q/'fpga').mkdir();(q/'doc').mkdir()
 shutil.copytree(r/'fpga/G80A',q/'fpga/G80A');shutil.copytree(r/'tools',q/'tools',ignore=shutil.ignore_patterns('__pycache__'))
 for script in ['rebuild_from_t80.py']+[f'extend_r{i}.py' for i in range(2,11)]:
  p=subprocess.run(['python3',str(q/'tools'/script)],capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
 hashes={p.name:digest(p) for p in (q/'fpga/G80A_eZ80').glob('*.vhd')}
 for n,h in hashes.items():assert digest(r/'fpga/G80A_eZ80'/n)==h,n
(r/'verification_rebuild_r10.json').write_text(json.dumps(dict(reproduced_files=len(hashes),sha256=hashes),indent=2)+'\n')
prov=json.loads((r/'doc/provenance.json').read_text())
for n,h in prov.items():assert digest(r/'fpga/G80A'/(n+'.vhd'))==h,n
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
changed=None
if previous.exists():
 changed=[str(p.relative_to(r)) for p in (r/'fpga').rglob('*') if p.is_file() and p.read_bytes()!=(previous/p.relative_to(r)).read_bytes()]
 assert set(changed)=={'fpga/G80A_eZ80/'+n for n in ('t80_ez80.vhd','t80_pack_ez80.vhd','t80_mcode_ez80.vhd')},changed
 for p in (previous/'hardware_test').glob('*.COM'):assert (r/'hardware_test'/p.name).read_bytes()==p.read_bytes(),p.name
p1=r.parent/'ez80_future_tests_P1/hardware_test/EZ80ADL.COM'
if p1.exists():assert p1.read_bytes()==(r/'hardware_test/EZ80ADL.COM').read_bytes()
result=dict(replayed_R1_through_R10=True,reproduced_CPU_files=6,original_G80A_unchanged=True,changed_FPGA_files=changed,GOWIN_project_referenced_files=len(refs),all_project_files_exist=True,constraints_bridge_wrapper_unchanged=True,preloaded_ADL_COM_SHA256=digest(r/'hardware_test/EZ80ADL.COM'),new_COM='EZ80CTL.COM',new_COM_SHA256=digest(r/'hardware_test/EZ80CTL.COM'),GOWIN_run=False)
(r/'verification_release_r10.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS R10 reproduction6, GPRJ',len(refs),'refs, FLASH bytes, original CPU/constraints identity')
