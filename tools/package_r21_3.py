from pathlib import Path
import argparse,json,zipfile,hashlib,shutil,difflib,xml.etree.ElementTree as ET
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();r=Path(__file__).resolve().parent.parent;v=r/'verification_r21_3';v.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
for n,c in [('mem_r4',9),('io2_com_r21',7)]:
 p=r/f'verification_{n}_result.json';j=json.loads(p.read_text());assert j['fresh_runs']==c;assert p.stat().st_mtime>=(r/'fpga/G80A_eZ80/g80a_ez80.vhd').stat().st_mtime;shutil.copyfile(p,v/p.name)
 for f in(r/f'verification_{n}').glob('*.log'):
  q=v/n/f.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(f,q)
p=r/'verification_vhdl93_result.json';assert p.is_file();shutil.copyfile(p,v/p.name)
p=r/'verification_mr4_r21_3/result.json';j=json.loads(p.read_text());assert j['verified_profiles']==8;shutil.copyfile(p,v/'mr4.json')
for f in(r/'verification_mr4_r21_3').glob('*.log'):
 assert 'PASS io2_com_r21' in f.read_text() and 'FATAL:'not in f.read_text(),f
 shutil.copyfile(f,v/f.name)
with zipfile.ZipFile(a.baseline)as z:
 prefix='MSXnano_T80_eZ80_restart_R21_2/';changed=[];patch=[];oldcom={};oldfpga=set()
 for n in z.namelist():
  if not n.startswith(prefix)or n.endswith('/'):continue
  rel=n[len(prefix):];p=r/rel
  if rel.startswith('fpga/'):
   oldfpga.add(rel)
   assert p.is_file(),rel
   if z.read(n)!=p.read_bytes():changed.append(rel);patch.extend(difflib.unified_diff(z.read(n).decode().splitlines(True),p.read_text().splitlines(True),fromfile='R21.2/'+rel,tofile='R21.3/'+rel))
  if rel.startswith('hardware_test/')and p.suffix.upper()in('.COM','.BAT'):
   assert z.read(n)==p.read_bytes(),rel
   if p.suffix.upper()=='.COM':oldcom[rel]=sha(p.read_bytes())
 assert set(changed)=={'fpga/G80A_eZ80/g80a_ez80.vhd','fpga/top_ez80.v','fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj'},changed
 added={str(p.relative_to(r))for p in(r/'fpga').rglob('*')if p.is_file()}-oldfpga
 assert added=={'fpga/src/ez80_trace_mux.v'},added
 changed+=sorted(added)
 assert len(oldcom)==31
(r/'R21_2_to_R21_3.patch').write_text(''.join(patch))
meta=json.loads((r/'hardware_test/EZ80MR4.json').read_text());assert sha((r/'EZ80MR4.COM').read_bytes())==sha((r/'hardware_test/EZ80MR4.COM').read_bytes())==meta['sha256']
summary=dict(version='R21.3 observation link comparison',baseline='R21.2 user hardware MEM/IO2/RUNALL PASS, SofaRun Space Manbow PLAY; MR3 CPU values correct but records zero',GOWIN_run=False,hardware_run=False,STA_closed=False,area_measured=False,CPU_implementation_unchanged=True,SDC_unchanged=True,SDRAM_controller_unchanged=True,bridge_unchanged=True,added_source_FF_bits_vs_R21_2=0,changed_or_added_FPGA_files=changed,unchanged_existing_COMs=oldcom,new_COM=meta['name'],new_COM_crc32=meta['crc32'],verified_profiles=24,profiles=dict(MR4=8,EZ80MEM=9,EZ80IO2=7),vhdl93='6 files',limitations='No GOWIN/physical timing reproduction. R21.2 zero-record cause remains unconfirmed. MR3 retained unchanged but returns NOT READY on new version.')
(v/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');fpga={str(p.relative_to(r)):sha(p.read_bytes())for p in sorted((r/'fpga').rglob('*'))if p.is_file()and'impl'not in p.parts and p.suffix.lower()!='.fs'};(r/'FPGA_SHA256.json').write_text(json.dumps(fpga,indent=2)+'\n')
prj=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=[(prj.parent/f.attrib['path'].replace('\\','/')).resolve()for f in ET.parse(prj).iter('File')if f.attrib.get('enable','1')=='1'];assert all(p.is_file()for p in refs)
files=[]
for p in r.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if rel==Path('SHA256SUMS.txt')or any(c in('impl','__pycache__','.git')for c in rel.parts)or p.suffix.lower()in('.vvp','.cf','.pyc','.fs'):continue
 if rel.parts[0].startswith('verification')and rel.parts[0]!='verification_r21_3':continue
 files.append(p)
(r/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(r))+'\n'for p in sorted(files)));files.append(r/'SHA256SUMS.txt');a.out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(a.out,'w',zipfile.ZIP_DEFLATED)as z:
 for p in sorted(files):z.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(a.out)as z:
 assert z.testzip()is None
 for line in z.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert sha(z.read(r.name+'/'+n))==h
 for p in refs:assert r.name+'/'+str(p.relative_to(r.resolve()))in z.namelist()
print('PASS package: 4 changed/added FPGA files, 31 unchanged COMs + MR4, 24 profiles, GPRJ and manifest validated')
