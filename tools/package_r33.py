from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1]
v=json.loads((R/'doc/R33_VALIDATION.json').read_text())
assert v['release']=='R33' and len(v['differential'])==43 and v['arithmetic']['cases']==395776
assert v['RTL_changed']==['fpga/G80A_eZ80/t80_ez80.vhd'] and v['COMs_unchanged']==30
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def included(p):
 rel=p.relative_to(R)
 if any(part in ['__pycache__','.git','impl']or part.startswith('verification')for part in rel.parts):return False
 return p.suffix not in ['.vvp','.pyc'] and not p.name.startswith('work-obj')
current={str(p.relative_to(R)):digest(p)for p in(R/'fpga').rglob('*')if p.is_file()}
assert current==v['FPGA_sha256'],'RTL changed after verification'
(R/'FPGA_SHA256.json').write_text(json.dumps(current,indent=2)+'\n')
files=[p for p in R.rglob('*')if p.is_file()and included(p)and p.name!='SHA256SUMS.txt']
(R/'SHA256SUMS.txt').write_text(''.join(digest(p)+'  '+str(p.relative_to(R))+'\n'for p in sorted(files)))
files.append(R/'SHA256SUMS.txt');z=R.parent/(R.name+'.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as f:
 for p in sorted(files):f.write(p,str(Path(R.name)/p.relative_to(R)))
with zipfile.ZipFile(z)as f:
 assert f.testzip()is None
 # Verify every release entry using the manifest stored inside the ZIP.
 sums=f.read(R.name+'/SHA256SUMS.txt').decode()
 for line in sums.splitlines():
  h,p=line.split('  ',1);assert hashlib.sha256(f.read(R.name+'/'+p)).hexdigest()==h,p
print(json.dumps(dict(path=str(z),bytes=z.stat().st_size,files=len(files),sha256=digest(z)),indent=2))
