"""Package the V34 source and hardware test; no generated FPGA bitstream."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,subprocess
r=Path(__file__).resolve().parent.parent
subprocess.run(['python3','tools/verify_release34.py'],cwd=r,check=True)
target=r.parent/'MSXnano_T80_eZ80_switch_v34.zip';root_name=target.stem
files=[]
for p in sorted(r.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if any(x.startswith('.') or x.startswith('verification') or x in ('__pycache__','node_modules') for x in rel.parts[:-1]):continue
 if p.name.startswith('.') or p.suffix in ('.pyc','.tmp','.vvp','.cf'):continue
 if 'impl' in rel.parts[:-1] and p.name!='device.cfg':continue
 files.append((p,root_name+'/'+rel.as_posix()))
temp=target.with_suffix('.tmp')
with ZipFile(temp,'w',ZIP_DEFLATED,compresslevel=9) as z:
 for p,name in files:z.write(p,name)
with ZipFile(temp) as z:
 assert z.testzip() is None
 for name in ('README.md','hardware_test/EZ80RAM.COM','hardware_test/ez80ram_v34.asm',
  'hardware_test/EZ80RAM_README_ja.md','doc/ADL_PROGRESS_v34.md','verification_result_v34.json',
  'test_results_com_v34.log','release_checks_v34.json','fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj'):
  assert root_name+'/'+name in z.namelist(),name
 assert not any('/impl/' in n and not n.endswith('/device.cfg') for n in z.namelist())
temp.replace(target)
result=dict(path=str(target),files=len(files),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(r.parent/'release_v34_archive.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
