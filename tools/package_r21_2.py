from pathlib import Path
import argparse,json,zipfile,hashlib,shutil,difflib,xml.etree.ElementTree as ET
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();r=Path(__file__).resolve().parent.parent;v=r/'verification_r21_2';v.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
for n,c in [('mem_r4',9),('io2_com_r21',7)]:
 p=r/f'verification_{n}_result.json';j=json.loads(p.read_text());assert j['fresh_runs']==c;assert p.stat().st_mtime>=(r/'fpga/G80A_eZ80/g80a_ez80.vhd').stat().st_mtime;shutil.copyfile(p,v/p.name)
 for f in(r/f'verification_{n}').glob('*.log'):
  q=v/n/f.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(f,q)
p=r/'verification_vhdl93_result.json';assert p.is_file();shutil.copyfile(p,v/p.name)
p=r/'verification_mr3_r21_2/verification.json';j=json.loads(p.read_text());assert len(j['profiles'])==5;shutil.copyfile(p,v/'mr3.json')
for f in(r/'verification_mr3_r21_2').glob('*.log'):shutil.copyfile(f,v/f.name)
p=r/'verification_mr3_guard_r21_2/result.json';g=json.loads(p.read_text());assert 'EZ80MR3 R21.2: NOT READY'in g['output'];shutil.copyfile(p,v/'guard.json')
for f in(r/'verification_mr3_guard_r21_2').glob('*.log'):shutil.copyfile(f,v/('guard_'+f.name))
with zipfile.ZipFile(a.baseline)as z:
 prefix='MSXnano_T80_eZ80_restart_R21_1/';changed=[];patch=[];oldcom={}
 for n in z.namelist():
  if not n.startswith(prefix)or n.endswith('/'):continue
  rel=n[len(prefix):];p=r/rel
  if rel.startswith('fpga/'):
   assert p.is_file(),rel
   if z.read(n)!=p.read_bytes():changed.append(rel);patch.extend(difflib.unified_diff(z.read(n).decode().splitlines(True),p.read_text().splitlines(True),fromfile='R21.1/'+rel,tofile='R21.2/'+rel))
  if rel.startswith('hardware_test/')and p.suffix.upper()in('.COM','.BAT'):
   assert z.read(n)==p.read_bytes(),rel
   if p.suffix.upper()=='.COM':oldcom[rel]=sha(p.read_bytes())
 assert set(changed)=={'fpga/G80A_eZ80/g80a_ez80.vhd','fpga/top_ez80.v','fpga/src/ez80_memory_bridge.v'},changed
 assert len(oldcom)==30
(r/'R21_1_to_R21_2.patch').write_text(''.join(patch))
meta=json.loads((r/'hardware_test/EZ80MR3.json').read_text());assert sha((r/'EZ80MR3.COM').read_bytes())==sha((r/'hardware_test/EZ80MR3.COM').read_bytes())==meta['sha256']
summary=dict(version='R21.2 diagnostic build',hardware_failure_cause='unresolved',GOWIN_run=False,hardware_run=False,STA_closed=False,area_measured=False,CPU_implementation_unchanged=True,SDC_unchanged=True,SDRAM_controller_unchanged=True,added_observation_FF_bits=31,changed_FPGA_files=changed,unchanged_existing_COMs=oldcom,new_COM=meta['name'],new_COM_crc32=meta['crc32'],fresh_profiles=22,profiles=dict(MR3=5,old_feature_guard=1,EZ80MEM=9,EZ80IO2=7),vhdl93='6 files',limitations='No gate-level/physical timing reproduction. Passive recording is not a hardware fix.')
(v/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');fpga={str(p.relative_to(r)):sha(p.read_bytes())for p in sorted((r/'fpga').rglob('*'))if p.is_file()and'impl'not in p.parts and p.suffix.lower()!='.fs'};(r/'FPGA_SHA256.json').write_text(json.dumps(fpga,indent=2)+'\n')
prj=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=[(prj.parent/f.attrib['path'].replace('\\','/')).resolve()for f in ET.parse(prj).iter('File')if f.attrib.get('enable','1')=='1'];assert all(p.is_file()for p in refs)
files=[]
for p in r.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if rel==Path('SHA256SUMS.txt')or any(c in('impl','__pycache__','.git')for c in rel.parts)or p.suffix.lower()in('.vvp','.cf','.pyc','.fs'):continue
 if rel.parts[0].startswith('verification')and rel.parts[0]!='verification_r21_2':continue
 files.append(p)
(r/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(r))+'\n'for p in sorted(files)));files.append(r/'SHA256SUMS.txt');a.out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(a.out,'w',zipfile.ZIP_DEFLATED)as z:
 for p in sorted(files):z.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(a.out)as z:
 assert z.testzip()is None
 for line in z.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert sha(z.read(r.name+'/'+n))==h
 for p in refs:assert r.name+'/'+str(p.relative_to(r.resolve()))in z.namelist()
print('PASS package: 3 changed FPGA files, 30 unchanged COMs + MR3, 22 profiles, GPRJ and manifest validated')
