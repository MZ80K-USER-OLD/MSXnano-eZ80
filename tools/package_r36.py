from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];v=json.loads((R/'doc/R36_VALIDATION.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert v['release']=='R36' and len(v['differential'])==42 and v['COMs_unchanged']==30
current={str(p.relative_to(R)):sha(p) for p in (R/'fpga').rglob('*') if p.is_file()}
assert current==v['scope']['FPGA_sha256'],'RTL changed after validation'
(R/'FPGA_SHA256.json').write_text(json.dumps(current,indent=2)+'\n')
def include(p):
 rel=p.relative_to(R)
 return not any(x in ['__pycache__','.git','impl'] for x in rel.parts) and not rel.parts[0].startswith('verification') and p.suffix not in ['.vvp','.pyc'] and not p.name.startswith('work-obj')
files=sorted(p for p in R.rglob('*') if p.is_file() and include(p) and p.name!='SHA256SUMS.txt')
(R/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+str(p.relative_to(R))+'\n' for p in files));files.append(R/'SHA256SUMS.txt');z=R.parent/(R.name+'.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
 for p in sorted(files):out.write(p,str(Path(R.name)/p.relative_to(R)))
with zipfile.ZipFile(z) as out:
 assert out.testzip() is None
 for line in out.read(R.name+'/SHA256SUMS.txt').decode().splitlines():
  h,p=line.split('  ',1);assert hashlib.sha256(out.read(R.name+'/'+p)).hexdigest()==h,p
print(json.dumps(dict(file=str(z.resolve()),bytes=z.stat().st_size,files=len(files),sha256=sha(z)),indent=2))
