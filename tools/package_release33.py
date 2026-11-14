"""Package the verified source release, excluding caches and stale build products."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,subprocess
r=Path(__file__).resolve().parent.parent
subprocess.run(['python3','tools/verify_release33.py'],cwd=r,check=True)
target=r.parent/'MSXnano_T80_eZ80_switch_v33.zip'
root_name='MSXnano_T80_eZ80_switch_v33'
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
 for name in ('README.md','verification_result_v33.json','release_checks_v33.json',
  'test_results_memory_v33.log','doc/ADL_PROGRESS_v33.md',
  'doc/MSXnano_eZ80_Memory_Allocation_v2.md','fpga/src/ez80_memory_bridge.v',
  'fpga/src/memory_ez80.v','fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj'):
  assert root_name+'/'+name in z.namelist(),name
 assert not any('/impl/' in n and not n.endswith('/device.cfg') for n in z.namelist())
temp.replace(target)
result=dict(path=str(target),files=len(files),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(r.parent/'release_v33_archive.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
