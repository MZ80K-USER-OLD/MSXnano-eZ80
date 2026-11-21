from pathlib import Path
import argparse,zipfile,hashlib,json,shutil,difflib,re,xml.etree.ElementTree as ET
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();r=Path(__file__).resolve().parent.parent;v=r/'verification_r22_2';v.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
checks=[('verification_ior_r22/result.json','ior_unit.json'),('verification_io2_r21_result.json','io2_unit.json'),('verification_ior_com_r22_result.json','ior_com.json'),('verification_mem_r4_result.json','mem.json'),('verification_board_r18_3_result.json','board.json'),('verification_vhdl93_result.json','vhdl93.json'),('verification_mr4_r22_smoke/result.json','mr4_smoke.json'),('verification_ior_diag_r22_1/result.json','small_diagnostics.json')]
for src,dst in checks:
 p=r/src;assert p.exists(),p;assert p.stat().st_mtime>=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').stat().st_mtime,p;shutil.copyfile(p,v/dst)
assert json.loads((v/'ior_unit.json').read_text())['cases']==648
assert json.loads((v/'ior_com.json').read_text())['fresh_runs']==7
assert json.loads((v/'small_diagnostics.json').read_text())['fresh_profiles']==12
assert json.loads((v/'mem.json').read_text())['fresh_runs']==9
for folder in ['verification_mcode_r22_2','verification_ior_r22','verification_io2_r21','verification_mem_r4','verification_board_r18_3','verification_ior_com_r22','verification_mr4_r22_smoke','verification_ior_diag_r22_1']:
 for p in(r/folder).glob('*.log'):
  q=v/folder/p.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(p,q)
for m in range(4):
 p=r/f'verification_mcode_r22_2/mode{m}.log';s=p.read_text();assert f'PASS mcode equivalence Mode={m} vectors=458752'in s
oldcom={};changed=[];diff=[]
with zipfile.ZipFile(a.baseline)as z:
 prefix=z.namelist()[0].split('/')[0]+'/'
 for n in z.namelist():
  if not n.startswith(prefix)or n.endswith('/'):continue
  rel=n[len(prefix):];p=r/rel
  if rel.startswith('fpga/'):
   assert p.is_file(),p
   if p.read_bytes()!=z.read(n):
    changed.append(rel);diff.extend(difflib.unified_diff(z.read(n).decode().splitlines(True),p.read_text().splitlines(True),fromfile='R22/'+rel,tofile='R22.2/'+rel))
  if rel.lower().endswith('.com'):
   assert p.read_bytes()==z.read(n),rel;oldcom[rel]=sha(p.read_bytes())
assert changed==['fpga/G80A_eZ80/t80_mcode_ez80.vhd'],changed
(r/'R22_to_R22_2.patch').write_text(''.join(diff))
fpga={str(p.relative_to(r)):sha(p.read_bytes())for p in(r/'fpga').rglob('*')if p.is_file()and'impl'not in p.parts};(r/'FPGA_SHA256.json').write_text(json.dumps(fpga,indent=2)+'\n');(r/'doc/R22_2_FPGA_SHA256.json').write_text(json.dumps(fpga,indent=2)+'\n')
for name in ('EZ80IR0','EZ80IR1','EZ80IR3'):
 j=json.loads((r/'hardware_test'/(name+'.json')).read_text());assert sha((r/(name+'.COM')).read_bytes())==j['sha256']==sha((r/'hardware_test'/(name+'.COM')).read_bytes())
prj=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=[(prj.parent/f.attrib['path'].replace('\\','/')).resolve()for f in ET.parse(prj).iter('File')if f.attrib.get('enable','1')=='1'];assert all(p.is_file()for p in refs)
for p in [r/'README.md',r/'doc/README.md',r/'doc/R22_2_ED_DECODE_COMPARISON.md']:
 for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://'not in dest and not dest.startswith('#'):assert(p.parent/dest.split('#')[0]).exists(),(p,dest)
summary=dict(version='R22.2 ED decode comparison',GOWIN_run=False,hardware_run=False,STA_closed=False,area_measured=False,physical_failure_root_cause_confirmed=False,changed_FPGA_files=changed,unchanged_COM_sha256=oldcom,small_diagnostic_COMs={name:sha((r/(name+'.COM')).read_bytes())for name in('EZ80IR0','EZ80IR1','EZ80IR3')},mcode_compared_vectors=1835008,mcode_modes=[0,1,2,3],mcode_configuration_patterns=64,mcode_scope='all outputs for all 256 raw opcodes, 4 ISet pages, 7 M-cycles, 64 selected patterns per Mode; consistent Write_Class; not formal unbounded equivalence',constraints_changed=False,wrapper_changed=False,bridge_changed=False,SDRAM_controller_changed=False,baseline_hardware_failures=dict(EZ80IOR='CASE0 freeze',EZ80IR0='stage0 ADDR=0EFFFF EXP=C3 ACT=7E',EZ80MEM='stage1 reported ADDR=07FFE EXP=31 ACT=7E; intended first test address07FFFE',RUNALL='FAIL present, details not supplied'),historical_precedent='R15.3 TST moved from global override into ED rows; later user CT1/D3/TST/MEM/game PASS',checks=[dst for src,dst in checks])
(v/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
files=[]
for p in sorted(r.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if rel==Path('SHA256SUMS.txt')or any(x in('impl','__pycache__','.git')for x in rel.parts)or p.suffix in('.vvp','.cf','.pyc','.fs'):continue
 if rel.parts[0].startswith('verification')and rel.parts[0]!='verification_r22_2':continue
 files.append(p)
(r/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(r))+'\n'for p in files));files.append(r/'SHA256SUMS.txt');a.out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.out,'w',zipfile.ZIP_DEFLATED)as z:
 for p in files:z.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(a.out)as z:
 assert z.testzip()is None
 for line in z.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert sha(z.read(r.name+'/'+n))==h
 for p in refs:assert r.name+'/'+str(p.relative_to(r.resolve()))in z.namelist()
print('PASS R22.2 ZIP: only mcode RTL changed, original COMs unchanged, 1835008 mcode comparisons; GPRJ/manifest verified; board/GOWIN not run')
