from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=json.loads((R/'doc/R37_VALIDATION.json').read_text());assert v['release']=='R37' and v['independent_instruction_cases']==10240 and v['FUSE_target_passed']==64 and len(v['existing_COM_runs'])==42
current={str(p.relative_to(R)):sha(p) for p in (R/'fpga').rglob('*') if p.is_file()};assert current==v['scope']['FPGA_sha256']
(R/'FPGA_SHA256.json').write_text(json.dumps(current,indent=2)+'\n')
# Runtime work directories and superseded trial outputs are never release files.
def include(p):
 rel=p.relative_to(R)
 if any(x in ['__pycache__','.git','impl'] for x in rel.parts) or rel.parts[0].startswith('verification'):return False
 if p.suffix in ['.vvp','.pyc','.cf','.so'] or p.name.startswith('work-obj'):return False
 if rel.parts[0]=='fuse_test' and len(rel.parts)>2 and rel.parts[1]=='results':
  if rel.parts[2] not in ['full_r37','events_r37','ldair_r37'] or p.name=='stimulus.txt':return False
 return p.name!='SHA256SUMS.txt'
files=sorted(p for p in R.rglob('*') if p.is_file() and include(p))
(R/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+str(p.relative_to(R))+'\n' for p in files));files.append(R/'SHA256SUMS.txt');z=R.parent/(R.name+'.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
 for p in sorted(files):f.write(p,str(Path(R.name)/p.relative_to(R)))
with zipfile.ZipFile(z) as f:
 assert f.testzip() is None
 for line in f.read(R.name+'/SHA256SUMS.txt').decode().splitlines():
  h,p=line.split('  ',1);assert hashlib.sha256(f.read(R.name+'/'+p)).hexdigest()==h,p
 assert f.read(R.name+'/EZ80IRF.COM')==f.read(R.name+'/hardware_test/EZ80IRF.COM')
 assert any(n.startswith(R.name+'/doc/R37_evidence/') for n in f.namelist())
print(json.dumps(dict(file=str(z.resolve()),bytes=z.stat().st_size,files=len(files),sha256=sha(z)),indent=2))
