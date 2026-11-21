from pathlib import Path
import argparse,zipfile,hashlib,json,shutil,difflib,re,collections,xml.etree.ElementTree as ET,zlib
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();r=Path(__file__).resolve().parent.parent;v=r/'verification_r22';v.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
# Aggregate current-run logs, including the normal COM run preceding the six further profiles.
logs=sorted((r/'verification_ior_com_r22').glob('*.log'));assert len(logs)==7
for p in logs:assert 'PASS ior_com_r22' in p.read_text() and 'FATAL:'not in p.read_text(),p
normal=r/'verification_ior_com_r22/4_0_0_0_1_1_0_0.log';assert 'EZ80IOR R22: PASS'in normal.read_text()
com_profiles=[]
for p in logs:
 q=v/'ior_com'/p.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(p,q);com_profiles.append(dict(profile=p.stem,output=p.read_text()))
checks=[('verification_ior_r22/result.json','ior_unit.json'),('verification_io2_r21_result.json','io2_unit.json'),('verification_io2_com_r21_result.json','io2_com.json'),('verification_mem_r4_result.json','mem.json'),('verification_board_r18_3_result.json','board.json'),('verification_prefix_r19_1_result.json','prefix.json'),('verification_im0_r19_result.json','im0.json'),('verification_vhdl93_result.json','vhdl93.json'),('verification_mr4_r22_smoke/result.json','mr4_smoke.json')]
for src,dst in checks:
 p=r/src;assert p.exists(),p;assert p.stat().st_mtime>=(r/'fpga/G80A_eZ80/t80_ez80.vhd').stat().st_mtime,p;shutil.copyfile(p,v/dst)
assert json.loads((v/'ior_unit.json').read_text())['cases']==648
assert json.loads((v/'mem.json').read_text())['fresh_runs']==9
for folder in ['verification_ior_r22','verification_io2_r21','verification_mem_r4','verification_board_r18_3','verification_prefix_r19_1','verification_im0_r19','verification_io2_com_r21','verification_mr4_r22_smoke']:
 for p in(r/folder).glob('*.log'):
  q=v/folder/p.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(p,q)
# Only the four documented CPU files may change; memory/bus/constraints/project stay byte-identical.
with zipfile.ZipFile(a.baseline)as z:
 prefix=z.namelist()[0].split('/')[0]+'/';changed=[];diff=[];oldcom={}
 for n in z.namelist():
  if not n.startswith(prefix)or n.endswith('/'):continue
  rel=n[len(prefix):];p=r/rel
  if rel.startswith('fpga/'):
   assert p.is_file(),rel
   if p.read_bytes()!=z.read(n):
    changed.append(rel);diff.extend(difflib.unified_diff(z.read(n).decode().splitlines(True),p.read_text().splitlines(True),fromfile='R21.3/'+rel,tofile='R22/'+rel))
  if rel.lower().endswith('.com'):
   assert p.read_bytes()==z.read(n),rel;oldcom[rel]=sha(p.read_bytes())
 assert set(changed)=={'fpga/G80A_eZ80/'+n+'_ez80.vhd'for n in('t80','t80_pack','t80_mcode','g80a')},changed
(r/'R21_3_to_R22.patch').write_text(''.join(diff))
meta=json.loads((r/'hardware_test/EZ80IOR.json').read_text());assert meta['sha256']==sha((r/'EZ80IOR.COM').read_bytes())==sha((r/'hardware_test/EZ80IOR.COM').read_bytes());assert meta['crc32']=='643ACD66';assert len(meta['cases'])==32
j=json.loads((r/'doc/EZ80_INSTRUCTION_STATUS_R22.json').read_text());assert len(j['items'])==97 and len({x['mnemonic']for x in j['items']})==97;assert dict(collections.Counter(x['status']for x in j['items']))=={k:n for k,n in j['counts'].items()if n}
for name,h in j['rtl_sha256'].items():assert sha((r/name).read_bytes())==h
prj=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=[(prj.parent/f.attrib['path'].replace('\\','/')).resolve()for f in ET.parse(prj).iter('File')if f.attrib.get('enable','1')=='1'];assert all(p.is_file()for p in refs)
fpga={str(p.relative_to(r)):sha(p.read_bytes())for p in(r/'fpga').rglob('*')if p.is_file()and'impl'not in p.parts};(r/'FPGA_SHA256.json').write_text(json.dumps(fpga,indent=2)+'\n')
summary=dict(version='R22',baseline='R21.3 user hardware PASS, Logic94%',GOWIN_run=False,hardware_run=False,area_measured=False,STA_closed=False,changed_FPGA_files=changed,unchanged_COM_sha256=oldcom,new_COM=meta,IOR_unit_cases=648,IOR_COM_profiles=com_profiles,other_results=[dst for src,dst in checks],constraints_changed=False,memory_bridge_changed=False,SDRAM_controller_changed=False,existing_COMs_changed=False)
(v/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
files=[]
for p in sorted(r.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if rel==Path('SHA256SUMS.txt')or any(x in('impl','__pycache__','.git')for x in rel.parts)or p.suffix in('.vvp','.cf','.pyc','.fs'):continue
 if rel.parts[0].startswith('verification')and rel.parts[0]!='verification_r22':continue
 files.append(p)
(r/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(r))+'\n'for p in files));files.append(r/'SHA256SUMS.txt');a.out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.out,'w',zipfile.ZIP_DEFLATED)as z:
 for p in files:z.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(a.out)as z:
 assert z.testzip()is None
 for line in z.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  h,n=line.split('  ',1);assert sha(z.read(r.name+'/'+n))==h
 for p in refs:assert r.name+'/'+str(p.relative_to(r.resolve()))in z.namelist()
 assert r.name+'/hardware_test/EZ80IOR.COM'in z.namelist()
print('PASS R22 ZIP: four CPU files changed, all existing COMs unchanged, GPRJ refs/manifest verified; GOWIN/board not run')
