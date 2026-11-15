from pathlib import Path
import argparse,json,hashlib,zipfile,difflib,shutil,xml.etree.ElementTree as ET
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);args=ap.parse_args()
r=Path(__file__).resolve().parent.parent;out=r.parent.parent/'r20-delivery';out.mkdir(exist_ok=True)
z=zipfile.ZipFile(args.baseline);prefix='MSXnano_T80_eZ80_restart_R19_1/'
names=['im0_r19','im0_edges_r19','im0_com_r19','rst_r18','mixed_r14','rst_interrupt_r18','irq_unit_r19','mem_r4','rw_diag_r18_3','board_r18_3','rst_com_r18','locked_r18_3','vhdl93','prefix_r19_1','prefix_com_r19_1','sleep_r20','sleep_com_r20']
counts=[1536,72,7,312,192,24,18,9,8,2,9,16,None,1952,7,244,7]
v=r/'verification_r20';v.mkdir(exist_ok=True)
summary={'release':'R20','baseline':'R19.1 user hardware confirmed','GOWIN_run':False,'hardware_run':False,'timing_closed':False,'area_measured':False,'new_CPU_state_bits_RTL':1,'new_diagnostic_state_bits_RTL':0,'new_FSM_states':0,'verification':{},'new_false_paths':0,'new_multicycle_paths':0}
folders={'im0_r19':'verification_im0_r19','im0_edges_r19':'verification_im0_edges_r19','im0_com_r19':'verification_im0_com_r19','rst_r18':'verification_rst_r18_final','mixed_r14':'verification_mixed_r14','rst_interrupt_r18':'verification_rst_interrupt_r18','irq_unit_r19':'verification_irq_unit_r19','mem_r4':'verification_mem_r4','rw_diag_r18_3':'verification_rw_diag_r18_3','board_r18_3':'verification_board_r18_3','rst_com_r18':'verification_rst_com_r18_final','vhdl93':'verification_vhdl93','prefix_r19_1':'verification_prefix_r19_1','prefix_com_r19_1':'verification_prefix_com_r19_1','sleep_r20':'verification_sleep_r20','sleep_com_r20':'verification_sleep_com_r20'}
for name,count in zip(names,counts):
 p=r/f'verification_{name}_result.json';j=json.loads(p.read_text())
 if count is not None:assert j['fresh_runs']==count,(name,j.get('fresh_runs'))
 assert p.stat().st_mtime >= (r/'fpga/G80A_eZ80/t80_ez80.vhd').stat().st_mtime,name
 if name in ('im0_r19','im0_edges_r19'):assert p.stat().st_mtime>=(r/'sim/tb_im0_r19.sv').stat().st_mtime,name
 summary['verification'][name]={'fresh_runs':j.get('fresh_runs'),'expected_failure_runs':j.get('expected_failure_runs',0)}
 shutil.copyfile(p,v/p.name)
 if name in folders:
  for q in (r/folders[name]).glob('*.log'):
   if name=='im0_r19' and '_op' in q.name:continue
   dest=v/folders[name]/q.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,dest)
summary['checked_scenarios']=sum((x['fresh_runs'] or 0)+x['expected_failure_runs'] for x in summary['verification'].values())
summary['model_and_job_evidence']='final_models_and_jobs.json'
summary['note']='Expected unsupported/READY/fault detection scenarios included; not every row is a COM PASS. Full MSX-DOS/BIOS and physical STA are not simulated.'
changed=[];patch=[]
for n in z.namelist():
 if not n.startswith(prefix+'fpga/') or n.endswith('/'):continue
 rel=n[len(prefix):];a=z.read(n);b=(r/rel).read_bytes()
 if a!=b:
  changed.append(rel);patch.extend(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
assert set(changed)=={'fpga/G80A_eZ80/t80_ez80.vhd','fpga/G80A_eZ80/g80a_ez80.vhd','fpga/G80A_eZ80/t80_pack_ez80.vhd','fpga/G80A_eZ80/t80_mcode_ez80.vhd'},changed
summary['changed_FPGA_files_vs_R19_1']=changed
summary['FPGA_sha256']={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((r/'fpga').rglob('*')) if p.is_file() and 'impl' not in p.parts and p.suffix.lower()!='.fs'}
oldcom={}
for n in z.namelist():
 if n.startswith(prefix+'hardware_test/') and n.upper().endswith('.COM'):
  rel=n[len(prefix):];assert (r/rel).read_bytes()==z.read(n),rel;oldcom[rel]=hashlib.sha256(z.read(n)).hexdigest()
summary['unchanged_existing_COMs']=oldcom
meta=json.loads((r/'hardware_test/EZ80SLP.json').read_text());assert hashlib.sha256((r/'hardware_test/EZ80SLP.COM').read_bytes()).hexdigest()==meta['sha256']
assert (r/'EZ80SLP.COM').read_bytes()==(r/'hardware_test/EZ80SLP.COM').read_bytes()
summary['SLP']={'production_wake':'RESET only','diagnostic_escape':'private D3, not normal IRQ/NMI','system_clock_stopped':False,'long_SDRAM_VRAM_retention_guaranteed':False,'CPU_refresh_dependency':'fpga/src/memory_ez80.v refresh is selected by bus_rfsh_n','autonomous_refresh_added':False}
summary['new_COM']={k:meta[k] for k in ('name','version','bytes','sha256','crc32')}
(v/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(r/'FPGA_SHA256.json').write_text(json.dumps(summary['FPGA_sha256'],indent=2)+'\n')
(r/'R19_1_to_R20.patch').write_text(''.join(patch))
prj=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj'
for x in ET.parse(prj).iter('File'):
 if x.attrib.get('enable','1')=='1':assert (prj.parent/x.attrib['path'].replace('\\','/')).is_file(),x.attrib
files=[]
for p in r.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(r)
 if rel==Path('SHA256SUMS.txt'):continue
 if any(x in ('impl','__pycache__','.git') for x in rel.parts):continue
 if rel.parts[0].startswith('verification') and rel.parts[0]!='verification_r20':continue
 if p.suffix.lower() in ('.vvp','.fs','.cf','.pyc'):continue
 files.append(p)
(r/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(r))+'\n' for p in sorted(files)))
files.append(r/'SHA256SUMS.txt')
full=out/'MSXnano_T80_eZ80_restart_R20.zip'
with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
 for p in sorted(files):zz.write(p,r.name+'/'+str(p.relative_to(r)))
with zipfile.ZipFile(full) as zz:
 assert zz.testzip() is None
 for line in zz.read(r.name+'/SHA256SUMS.txt').decode().splitlines():
  digest,name=line.split('  ',1);assert hashlib.sha256(zz.read(r.name+'/'+name)).hexdigest()==digest,name
 for x in ET.parse(prj).iter('File'):
  if x.attrib.get('enable','1')=='1':assert r.name+'/'+str((prj.parent/x.attrib['path'].replace('\\','/')).resolve().relative_to(r.resolve())) in zz.namelist()
 assert not any('/impl/' in x or x.endswith(('.fs','.vvp')) for x in zz.namelist())
shutil.copyfile(r/'doc/R20_README.md',out/'EZ80_R20_README.md')
tests=out/'MSXnano_eZ80_R20_tests.zip'
with zipfile.ZipFile(tests,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zz:
 for p in sorted((r/'hardware_test').glob('*.COM')):zz.write(p,p.name)
 for p in sorted((r/'hardware_test').glob('*.BAT')):zz.write(p,p.name)
 zz.writestr('README.md',(r/'doc/R20_README.md').read_text())
 zz.writestr('EZ80SLP.json',(r/'hardware_test/EZ80SLP.json').read_bytes())
with zipfile.ZipFile(tests) as zz:
 assert zz.testzip() is None
 assert len([x for x in zz.namelist() if x.endswith('.COM')])==29
 for name,digest in oldcom.items():assert hashlib.sha256(zz.read(Path(name).name)).hexdigest()==digest
 assert hashlib.sha256(zz.read('EZ80SLP.COM')).hexdigest()==meta['sha256']
print('PASS R20 package',summary['checked_scenarios'],'scenarios;',len(oldcom),'unchanged COMs + EZ80SLP;',full.stat().st_size,'bytes')
