from pathlib import Path
import zipfile,json,hashlib,shutil,xml.etree.ElementTree as ET,difflib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--r21',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
r=Path(__file__).resolve().parent.parent;v=r/'verification_r21_1';v.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
counts={'io2_r21':244,'io2_com_r21':7,'mem_r4':9,'rw_diag_r18_3':8,'irq_r11':7,'locked_r18_3':16,'prefix_com_r19_1':7,'im0_com_r19':7,'nop_com_r20_6':7}
results={}
for n,count in counts.items():
 p=r/('verification_'+n+'_result.json');j=json.loads(p.read_text());assert j['fresh_runs']==count,(n,j)
 assert p.stat().st_mtime>=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').stat().st_mtime
 shutil.copyfile(p,v/p.name);results[n]=count
 for f in (r/('verification_'+n)).glob('*.log'):
  q=v/n/f.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(f,q)
p=r/'verification_vhdl93_result.json';assert p.is_file();shutil.copyfile(p,v/p.name)
for m in range(4):
 p=r/'verification_mcode_r21_1'/f'mode{m}.log';assert f'PASS mcode equivalence Mode={m} vectors=458752'in p.read_text();shutil.copyfile(p,v/p.name)
assert sum(results.values())==312
with zipfile.ZipFile(args.r21)as z:
 prefix='MSXnano_T80_eZ80_restart_R21/';changed=[];patch=[];unchanged_com=0
 for n in z.namelist():
  if not n.startswith(prefix)or n.endswith('/'):continue
  rel=n[len(prefix):];p=r/rel
  if rel.startswith('fpga/'):
   assert p.is_file(),rel
   if z.read(n)!=p.read_bytes():changed.append(rel);patch.extend(difflib.unified_diff(z.read(n).decode().splitlines(True),p.read_text().splitlines(True),fromfile='R21/'+rel,tofile='R21.1/'+rel))
  if rel.startswith('hardware_test/')and p.suffix.upper()in('.COM','.BAT'):
   assert z.read(n)==p.read_bytes(),rel
   if p.suffix.upper()=='.COM':unchanged_com+=1
 assert sorted(changed)==sorted(['fpga/G80A_eZ80/t80_mcode_ez80.vhd','fpga/G80A_eZ80/g80a_ez80.vhd']),changed
 assert unchanged_com==30
(r/'R21_to_R21_1.patch').write_text(''.join(patch))
summary=dict(version='R21.1',purpose='comparison build removing global IO2 opcode rewrite; R21 hardware failure cause unresolved',GOWIN_run=False,hardware_run=False,timing_closed=False,area_measured=False,changed_FPGA_files_vs_R21=changed,unchanged_R21_COMs=unchanged_com,COMs_changed=False,verification=results,conditions_profiles=312,mcode_compared_vectors=1835008,mcode_comparison='selected binary inputs, all control outputs vs R21, not formal equivalence',R21_report='doc/R21_IMPL_ANALYSIS.md',failed_user_MEM=dict(stage=1,address='07FFFE',expected='31',actual='7E'),failed_user_IO2='stops CASE 0')
(v/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
fpga={str(p.relative_to(r)):sha(p.read_bytes())for p in sorted((r/'fpga').rglob('*'))if p.is_file()and'impl'not in p.parts and p.suffix.lower()!='.fs'};(r/'FPGA_SHA256.json').write_text(json.dumps(fpga,indent=2)+'\n')
prj=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=[(prj.parent/f.attrib['path'].replace('\\','/')).resolve()for f in ET.parse(prj).iter('File')if f.attrib.get('enable','1')=='1'];assert all(p.is_file()for p in refs)
files=[]
for p in r.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if rel==Path('SHA256SUMS.txt')or any(a in ('impl','__pycache__','.git')for a in rel.parts)or p.suffix.lower()in('.vvp','.cf','.fs','.pyc'):continue
 if rel.parts[0].startswith('verification')and rel.parts[0]!='verification_r21_1':continue
 files.append(p)
(r/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(r))+'\n'for p in sorted(files)));files.append(r/'SHA256SUMS.txt')
args.out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(args.out,'w',zipfile.ZIP_DEFLATED)as z:
 for p in sorted(files):z.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(args.out)as z:
 assert z.testzip()is None
 for line in z.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert sha(z.read(r.name+'/'+n))==h,n
 for p in refs:assert r.name+'/'+str(p.relative_to(r.resolve()))in z.namelist()
print('PASS package: 2 changed FPGA files, 30 unchanged COMs, 312 conditions/profiles, 1835008 mcode vectors, GPRJ refs and manifest verified')
