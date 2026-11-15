from pathlib import Path
import argparse,json,hashlib,zipfile,difflib,shutil,xml.etree.ElementTree as ET
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);args=ap.parse_args()
r=Path(__file__).resolve().parent.parent;out=r.parent.parent/'r20_6-delivery';out.mkdir(exist_ok=True);base='MSXnano_T80_eZ80_restart_R19_1/';z=zipfile.ZipFile(args.baseline);sha=lambda b:hashlib.sha256(b).hexdigest()
v=r/'verification_r20_6';v.mkdir(exist_ok=True)
profiles={'nop_decode_r20_6':(580,'verification_nop_decode_r20_6'),'nop_com_r20_6':(7,'verification_nop_com_r20_6'),'mem_r4':(9,'verification_mem_r4'),'rw_diag_r18_3':(8,'verification_rw_diag_r18_3'),'irq_r11':(7,'verification_irq_r11'),'locked_r18_3':(16,None),'vhdl93':(None,'verification_vhdl93'),'prefix_com_r19_1':(7,'verification_prefix_com_r19_1'),'im0_com_r19':(7,'verification_im0_com_r19')}
summary=dict(release='R20.6 SLP NOP / TRAP excluded',baseline='R19.1 hardware-confirmed source',GOWIN_run=False,hardware_run=False,timing_closed=False,area_measured=False,new_CPU_state_bits=0,new_memory_state_bits=0,SLP='unsupported: unlocked NOP, locked legacy IM1 alias',TRAP='intentionally not implemented by user decision',verification={})
for name,(count,folder)in profiles.items():
 p=r/f'verification_{name}_result.json';j=json.loads(p.read_text());assert count is None or j['fresh_runs']==count,(name,j)
 assert p.stat().st_mtime>=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').stat().st_mtime,name
 summary['verification'][name]=dict(fresh_runs=j.get('fresh_runs'),expected_failure_runs=j.get('expected_failure_runs',0));shutil.copyfile(p,v/p.name)
 if folder:
  for p in (r/folder).glob('*.log'):
   q=v/folder/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
summary['checked_conditions_and_scenarios']=sum((a['fresh_runs']or 0)+a['expected_failure_runs']for a in summary['verification'].values())
summary['note']='580 combinational decode/control conditions plus 61 COM/behavioral profiles; includes expected READY/NOT READY/UNSUPPORTED/fault results. Not full ISA equivalence or physical timing.'
changed=[];patch=[];oldcom={}
for n in z.namelist():
 if not n.startswith(base)or n.endswith('/'):continue
 rel=n[len(base):]
 if rel.startswith('hardware_test/')and rel.endswith('.COM'):
  assert z.read(n)==(r/rel).read_bytes(),rel;oldcom[rel]=sha(z.read(n))
 if rel.startswith('fpga/')and z.read(n)!=(r/rel).read_bytes():
  changed.append(rel);patch.extend(difflib.unified_diff(z.read(n).decode().splitlines(True),(r/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
assert set(changed)=={'fpga/G80A_eZ80/t80_mcode_ez80.vhd','fpga/G80A_eZ80/g80a_ez80.vhd'},changed
assert len(oldcom)==28
assert (r/'hardware_test/RUNALL.BAT').read_bytes()==z.read(base+'hardware_test/RUNALL.BAT')+b'EZ80NP6 /RUN\r\n'
for p in (r/'fpga/G80A_eZ80').glob('*.vhd'):assert 'Sleep_FF'not in p.read_text()and'SLP_Wake_Req'not in p.read_text()
assert 'SLEEP_REFRESH'not in(r/'fpga/src/memory_ez80.v').read_text()
summary['changed_FPGA_files_vs_R19_1']=changed;summary['unchanged_existing_COMs']=oldcom
m=json.loads((r/'hardware_test/EZ80NP6.json').read_text());assert sha((r/'EZ80NP6.COM').read_bytes())==sha((r/'hardware_test/EZ80NP6.COM').read_bytes())==m['sha256'];summary['new_COM']={k:m[k]for k in ('name','version','bytes','sha256','crc32')}
summary['FPGA_sha256']={str(p.relative_to(r)):sha(p.read_bytes())for p in sorted((r/'fpga').rglob('*'))if p.is_file()and'impl'not in p.parts and p.suffix.lower()!='.fs'}
(v/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');(r/'FPGA_SHA256.json').write_text(json.dumps(summary['FPGA_sha256'],indent=2)+'\n');(r/'R19_1_to_R20_6.patch').write_text(''.join(patch));(r/'doc/R19_1_BASELINE_SUMMARY.json').write_bytes(z.read(base+'verification_r19_1/summary.json'))
prj=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=[(prj.parent/a.attrib['path'].replace('\\','/')).resolve()for a in ET.parse(prj).iter('File')if a.attrib.get('enable','1')=='1'];assert all(p.is_file()for p in refs)
files=[]
for p in r.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if rel==Path('SHA256SUMS.txt')or any(x in('impl','__pycache__','.git')for x in rel.parts)or p.suffix.lower()in('.vvp','.fs','.cf','.pyc'):continue
 if rel.parts[0].startswith('verification')and rel.parts[0]!='verification_r20_6':continue
 files.append(p)
(r/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(r))+'\n'for p in sorted(files)));files.append(r/'SHA256SUMS.txt')
full=out/'MSXnano_T80_eZ80_restart_R20_6.zip'
with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as zz:
 for p in sorted(files):zz.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(full)as zz:
 assert zz.testzip()is None
 for line in zz.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert sha(zz.read(r.name+'/'+n))==h,n
 for p in refs:assert r.name+'/'+str(p.relative_to(r.resolve()))in zz.namelist()
shutil.copyfile(r/'doc/R20_6_README.md',out/'EZ80_R20_6_README.md')
with zipfile.ZipFile(out/'MSXnano_eZ80_R20_6_tests.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9)as zz:
 for p in sorted((r/'hardware_test').glob('*.COM')):zz.write(p,p.name)
 for p in sorted((r/'hardware_test').glob('*.BAT')):zz.write(p,p.name)
 zz.write(r/'doc/R20_6_README.md','README.md');zz.write(r/'hardware_test/EZ80NP6.json','EZ80NP6.json')
with zipfile.ZipFile(out/'MSXnano_eZ80_R20_6_tests.zip')as zz:
 assert zz.testzip()is None;assert len([n for n in zz.namelist()if n.endswith('.COM')])==29
 for n,h in oldcom.items():assert sha(zz.read(Path(n).name))==h
 assert sha(zz.read('EZ80NP6.COM'))==m['sha256']
print('PASS R20.6 package',summary['checked_conditions_and_scenarios'],'conditions/profiles, 28 unchanged COMs + NP6, two FPGA files changed vs R19.1')
