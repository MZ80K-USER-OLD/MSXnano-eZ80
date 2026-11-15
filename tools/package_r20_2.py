from pathlib import Path
import argparse,json,hashlib,zipfile,difflib,shutil,xml.etree.ElementTree as ET
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);args=ap.parse_args()
r=Path(__file__).resolve().parent.parent;out=r.parent.parent/'r20_2-delivery';out.mkdir(exist_ok=True);z=zipfile.ZipFile(args.baseline);base='MSXnano_T80_eZ80_restart_R20_1/'
sha=lambda b:hashlib.sha256(b).hexdigest()
v=r/'verification_r20_2';v.mkdir(exist_ok=True)
profiles={'diag_r20_2':(14,'verification_diag_r20_2'),'sleep_com_r20':(7,'verification_sleep_com_r20'),'refresh_com_r20_1':(7,'verification_refresh_com_r20_1'),'mem_r4':(9,'verification_mem_r4'),'rw_diag_r18_3':(8,'verification_rw_diag_r18_3'),'irq_r11':(7,'verification_irq_r11'),'locked_r18_3':(16,None),'vhdl93':(None,'verification_vhdl93'),'top_refresh_r20_1':(1,'verification_top_refresh_r20_1'),'legacy_refresh_r20_1':(4,'verification_legacy_refresh_r20_1'),'refresh_r20_1':(5,'verification_refresh_r20_1')}
summary=dict(release='R20.2 diagnostic candidate',baseline='R20.1 user reported SLP freeze and REF screen corruption; last stable board baseline R19.1',GOWIN_run=False,hardware_run=False,physical_root_cause_confirmed=False,timing_closed=False,area_measured=False,new_architectural_CPU_bits=0,new_logical_control_bits=0,verification={})
for n,(count,folder)in profiles.items():
 p=r/f'verification_{n}_result.json';j=json.loads(p.read_text());assert count is None or j['fresh_runs']==count,(n,j)
 summary['verification'][n]=dict(fresh_runs=j.get('fresh_runs'),expected_failure_runs=j.get('expected_failure_runs',0));shutil.copyfile(p,v/p.name)
 if folder:
  for p in (r/folder).glob('*.log'):
   q=v/folder/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
summary['checked_scenarios']=sum((j['fresh_runs']or 0)+j['expected_failure_runs']for j in summary['verification'].values())
summary['prior_protocol_expected_failure_runs']=1
summary['note']='Includes expected READY/NOT READY/UNSUPPORTED/fault-detection cases. CPU ISA suites not rerun in this release are not counted. New RF2 timer is accelerated 128x in board simulation; separate controller test runs >64ms.'
summary['unchanged_existing_COMs']={};changed=[];patch=[]
for n in z.namelist():
 if not n.startswith(base)or n.endswith('/'):continue
 rel=n[len(base):]
 if rel.startswith('hardware_test/')and rel.endswith('.COM'):
  assert z.read(n)==(r/rel).read_bytes(),rel;summary['unchanged_existing_COMs'][rel]=sha(z.read(n))
 if rel.startswith('fpga/')and z.read(n)!=(r/rel).read_bytes():
  changed.append(rel);patch.extend(difflib.unified_diff(z.read(n).decode().splitlines(True),(r/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
assert set(changed)=={'fpga/G80A_eZ80/g80a_ez80.vhd'},changed
summary['changed_FPGA_files_vs_R20_1']=changed;summary['FPGA_sha256']={str(p.relative_to(r)):sha(p.read_bytes())for p in sorted((r/'fpga').rglob('*'))if p.is_file()and 'impl'not in p.parts and p.suffix.lower()!='.fs'}
summary['new_COMs']=[json.loads((r/'hardware_test'/(name+'.json')).read_text())for name in ['EZ80SL2','EZ80RF2']]
for m in summary['new_COMs']:assert sha((r/(m['name']+'.COM')).read_bytes())==m['sha256']
assert len(summary['unchanged_existing_COMs'])==30
(r/'R20_1_to_R20_2.patch').write_text(''.join(patch));(r/'FPGA_SHA256.json').write_text(json.dumps(summary['FPGA_sha256'],indent=2)+'\n');(v/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(r/'doc/R20_1_BASELINE_SUMMARY.json').write_bytes(z.read(base+'verification_r20_1/summary.json'))
prj=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj'
refs=[(prj.parent/a.attrib['path'].replace('\\','/')).resolve()for a in ET.parse(prj).iter('File')if a.attrib.get('enable','1')=='1'];assert all(p.is_file()for p in refs)
fs=[]
for p in r.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if rel==Path('SHA256SUMS.txt')or any(x in('impl','__pycache__','.git')for x in rel.parts)or p.suffix.lower()in('.vvp','.fs','.cf','.pyc'):continue
 if rel.parts[0].startswith('verification')and rel.parts[0]!='verification_r20_2':continue
 fs.append(p)
(r/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(r))+'\n'for p in sorted(fs)));fs.append(r/'SHA256SUMS.txt')
full=out/'MSXnano_T80_eZ80_restart_R20_2.zip'
with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as zz:
 for p in sorted(fs):zz.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(full)as zz:
 assert zz.testzip()is None
 for line in zz.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert sha(zz.read(r.name+'/'+n))==h,n
 for p in refs:assert r.name+'/'+str(p.relative_to(r.resolve()))in zz.namelist()
shutil.copyfile(r/'doc/R20_2_README.md',out/'EZ80_R20_2_README.md')
tests=out/'MSXnano_eZ80_R20_2_tests.zip'
with zipfile.ZipFile(tests,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as zz:
 for p in sorted((r/'hardware_test').glob('*.COM')):zz.write(p,p.name)
 for p in sorted((r/'hardware_test').glob('*.BAT')):zz.write(p,p.name)
 zz.write(r/'doc/R20_2_README.md','README.md');zz.write(r/'hardware_test/EZ80SL2.json','EZ80SL2.json');zz.write(r/'hardware_test/EZ80RF2.json','EZ80RF2.json')
with zipfile.ZipFile(tests)as zz:
 assert zz.testzip()is None;assert len([n for n in zz.namelist()if n.endswith('.COM')])==32
 for n,h in summary['unchanged_existing_COMs'].items():assert sha(zz.read(Path(n).name))==h
 
 for m in summary['new_COMs']:assert sha(zz.read(m['name']+'.COM'))==m['sha256']
print('PASS R20.2 package',summary['checked_scenarios'],'checks, 30 unchanged COMs + SL2/RF2')
