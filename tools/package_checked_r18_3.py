from pathlib import Path
import json, hashlib, zipfile, difflib, shutil, zlib
r=Path(__file__).resolve().parent.parent
out=r.parent.parent/'r18_3-delivery';out.mkdir(exist_ok=True)
z=zipfile.ZipFile(r.parent.parent/'rst-audit-input/MSXnano_T80_eZ80_restart_R18.zip')
selected=['rst_r18','mixed_r14','rst_interrupt_r18','irq_unit_r11','mem_r4','rw_diag_r18_3','board_r18_3','rst_com_r18','locked_r18_3','vhdl93']
expected=[312,192,24,18,9,8,2,1,16,None]
summary={'release':'R18.3','status':'simulation verified; comparison RTL; hardware cause unresolved','GOWIN_run':False,'hardware_run':False,'timing_closed':False,'LUT_change_measured':False,'RTL_added_control_register_bits':1,'new_false_paths':0,'new_multicycle_paths':0,'verification':{}}
v=r/'verification_r18_3';v.mkdir(exist_ok=True)
for name,count in zip(selected,expected):
 p=r/f'verification_{name}_result.json';j=json.loads(p.read_text())
 assert p.stat().st_mtime >= (r/'fpga/G80A_eZ80/t80_ez80.vhd').stat().st_mtime,name
 if 'sha256' in j and 'fpga/G80A_eZ80/t80_ez80.vhd' in j['sha256']:
  assert j['sha256']['fpga/G80A_eZ80/t80_ez80.vhd']==hashlib.sha256((r/'fpga/G80A_eZ80/t80_ez80.vhd').read_bytes()).hexdigest(),name
 if count is not None:assert j['fresh_runs']==count,(name,j)
 summary['verification'][name]={'fresh_runs':j.get('fresh_runs'),'expected_failure_runs':j.get('expected_failure_runs',0)}
 shutil.copyfile(p,v/p.name)
 # Store logs from this run, never the large compiled simulators.
 folder={'rst_r18':'verification_rst_r18_final','mixed_r14':'verification_mixed_r14','rst_interrupt_r18':'verification_rst_interrupt_r18','irq_unit_r11':'verification_irq_unit_r11','mem_r4':'verification_mem_r4','rw_diag_r18_3':'verification_rw_diag_r18_3','board_r18_3':'verification_board_r18_3','rst_com_r18':'verification_rst_com_r18_final','vhdl93':'verification_vhdl93'}.get(name)
 if folder:
  for q in (r/folder).glob('*.log'):
   dst=v/folder/q.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,dst)
summary['checked_scenarios']=sum(x['fresh_runs'] or 0 for x in summary['verification'].values())+sum(x['expected_failure_runs'] for x in summary['verification'].values())
summary['notes']=['Expected status/fault detection scenarios included; not all rows mean a COM PASS.','Unit/mixed four injected frame faults; MEM four faults and RW two faults are expected.','GHDL/Icarus model asserts registered RST request equals original R18 request at accepted T4.','Full MSX-DOS/BIOS and physical FPGA timing are not simulated.']
changed=[];patch=[]
for n in z.namelist():
 if '/fpga/' not in n or n.endswith('/'):continue
 rel=n.split('/',1)[1];a=z.read(n);b=(r/rel).read_bytes()
 if a!=b:
  changed.append(rel)
  patch.extend(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
assert changed==['fpga/G80A_eZ80/t80_ez80.vhd','fpga/tang20k.sdc'],changed
summary['changed_FPGA_files_vs_R18']=changed
summary['FPGA_sha256']={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((r/'fpga').rglob('*')) if p.is_file() and 'impl' not in p.parts and p.suffix.lower()!='.fs'}
coms={}
for n in z.namelist():
 if '/hardware_test/' in n and n.upper().endswith('.COM'):
  rel=n.split('/',1)[1];assert (r/rel).read_bytes()==z.read(n),rel
  coms[rel]=hashlib.sha256(z.read(n)).hexdigest()
rw=(r/'hardware_test/EZ80RW2.COM').read_bytes();assert hashlib.sha256(rw).hexdigest()=='d7cc5690f5e117ad7739fc395f4f77d6833705808d1cc9a7514d61f240ba048c'
coms['hardware_test/EZ80RW2.COM']=hashlib.sha256(rw).hexdigest()
summary['unchanged_published_COMs']=coms;summary['RW2_CRC32']=f'{zlib.crc32(rw):08X}'
(v/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(r/'FPGA_SHA256.json').write_text(json.dumps(summary['FPGA_sha256'],indent=2)+'\n')
(r/'R18_to_R18_3.patch').write_text(''.join(patch))
shutil.copyfile(r/'doc/R18_3_README.md',out/'EZ80_R18_3_README.md')
# Root historical verification outputs and binary simulator products are not current evidence.
files=[]
for p in r.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(r);parts=rel.parts
 if rel==Path('SHA256SUMS.txt'):continue
 if any(x in ('__pycache__','.git','impl') for x in parts):continue
 if parts[0].startswith('verification') and parts[0]!='verification_r18_3':continue
 if p.suffix.lower() in ('.vvp','.fs','.cf','.pyc'):continue
 files.append(p)
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(r))+'\n' for p in sorted(files))
(r/'SHA256SUMS.txt').write_text(manifest)
# Exclude any old manifest from the selection before adding the final manifest once.
files=[p for p in files if p.relative_to(r)!=Path('SHA256SUMS.txt')]+[r/'SHA256SUMS.txt']
output=out/'MSXnano_T80_eZ80_restart_R18_3.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
 for p in sorted(files):zz.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(output) as zz:
 assert zz.testzip() is None
 for line in zz.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  digest,name=line.split('  ',1)
  if name=='SHA256SUMS.txt':continue
  assert hashlib.sha256(zz.read(r.name+'/'+name)).hexdigest()==digest,name
 for name in coms:assert hashlib.sha256(zz.read(r.name+'/'+name)).hexdigest()==coms[name]
 assert not any('/impl/' in n or n.endswith(('.vvp','.fs')) for n in zz.namelist())
print('PASS package',output,'bytes',output.stat().st_size,'scenarios',summary['checked_scenarios'],'COMs',len(coms))
