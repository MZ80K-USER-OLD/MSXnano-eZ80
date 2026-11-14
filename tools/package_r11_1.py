from pathlib import Path
import json,hashlib,zipfile
r=Path(__file__).resolve().parent.parent;out=r.parent/'r11-1-delivery';out.mkdir(exist_ok=True)
j=json.loads((r/'verification_result.json').read_text());assert j['series']=='restart R11.1' and j['total_fresh_simulation_runs']==212 and j['expected_failure_runs']==4
files={}
for folder in ['fpga','hardware_test','sim','tools','doc']:
 for p in (r/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.cf','.vvp'] and p.name!='SHA256SUMS.txt':files[str(p.relative_to(r))]=p.read_bytes()
files['README.md']=(r/'README.md').read_bytes();files['verification_result.json']=(r/'verification_result.json').read_bytes()
for p in r.glob('verification*.json'):
 if p.name!='verification_result.json':files['verification_groups/'+p.name]=p.read_bytes()
for folder in r.glob('verification*'):
 if folder.is_dir():
  for p in folder.rglob('*.log'):files['verification_logs/'+str(p.relative_to(r))]=p.read_bytes()
coms=list((r/'hardware_test').glob('*.COM'));assert len(coms)==20
for p in coms:files[p.name]=p.read_bytes()
manifest=''.join(hashlib.sha256(v).hexdigest()+'  '+n+'\n' for n,v in sorted(files.items()));files['doc/SHA256SUMS.txt']=manifest.encode();(r/'doc/SHA256SUMS.txt').write_text(manifest)
base='MSXnano_T80_eZ80_restart_R11_1';p=out/(base+'.zip')
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(files.items()):z.writestr(base+'/'+n,v)
 for f in sorted(coms):z.writestr(f.name,f.read_bytes())
 for f in sorted((r/'hardware_test').glob('*.BAT')):z.writestr(f.name,f.read_bytes())
 z.writestr('EZ80_R11_1_README.md',(r/'README.md').read_bytes())
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 for n,v in files.items():assert z.read(base+'/'+n)==v,n
 for f in coms:
  for n in [f.name,base+'/'+f.name,base+'/hardware_test/'+f.name]:assert z.read(n)==f.read_bytes(),n
 record=dict(zip_bytes=p.stat().st_size,zip_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),members=len(z.namelist()),COM_count=20,COM_copies_per_test=3,all_CRC_and_member_bytes_verified=True)
(out/'EZ80_R11_1_README.md').write_bytes((r/'README.md').read_bytes());(out/'release.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
