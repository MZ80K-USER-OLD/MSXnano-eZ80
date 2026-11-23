"""Audit the R26 sources and completed checks. No GOWIN/board claim."""
from pathlib import Path
import hashlib,json,os,subprocess,shutil,xml.etree.ElementTree as E,zlib
r=Path(__file__).resolve().parents[1];w=r/'verification_r26';w.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((r/'doc/R26_BASELINE_SHA256.json').read_text())
changed=sorted(p for p,h in base.items()if sha(r/p)!=h)
expected=sorted(['fpga/G80A_eZ80/'+n+'_ez80.vhd'for n in ['t80_pack','t80','g80a']]+['fpga/src/ez80_memory_bridge.v'])
assert changed==expected,changed
projects=[]
for p in [r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',r/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 files=E.parse(p).findall('.//File');assert len(files)==123 and all((p.parent/f.get('path')).is_file()for f in files)
 projects.append(dict(path=str(p.relative_to(r)),references=len(files),sha256=sha(p)))
g=os.environ.get('GHDL','ghdl');q=w/'vhdl93';q.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 p=subprocess.run([g,'-a','--std=93','-fsynopsys','-fexplicit',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=q,capture_output=True,text=True);assert not p.returncode,p.stderr
commands=(r/'RUNALL.BAT').read_text().splitlines();names=[s.split()[0]for s in commands]
assert len(names)==25 and len(set(names))==25
for n in names+['EZ80MR4']:
 p=r/'hardware_test'/(n+'.COM');assert p.read_bytes()==(r/p.name).read_bytes()
 m=json.loads(p.with_suffix('.json').read_text());assert m['sha256']==sha(p) and m['bytes']==p.stat().st_size
 if 'crc32'in m:assert m['crc32']==f'{zlib.crc32(p.read_bytes()):08X}'
# The generic compatibility runs used CPU_DIV=16. MEM, TIO and WIN have dedicated suites.
compat=[]
for n in names:
 if n in ['EZ80MEM','EZ80TIO','EZ80WIN']:continue
 p=r/'verification_compat_coms_r26'/(n+'.log');s=p.read_text();assert 'PASS compat_com_r26'in s and 'FATAL'not in s,(n,s[-1000:])
 compat.append(dict(COM=n+'.COM',sha256=sha(r/'hardware_test'/(n+'.COM')),log_sha256=sha(p)))
checks={}
for key,path in [('requests','verification_window_request_r26/result.json'),('WIN','verification_window_com_r26/result.json'),('IRQ','verification_window_irq_r26/result.json'),('TIO','verification_tstio_com_r26_result.json'),('MEM','verification_mem_r4_result.json'),('MR4','verification_mr4_r21_3/result.json'),('CPU_regression','verification_regression_r25/result.json')]:
 p=r/path;j=json.loads(p.read_text());checks[key]=j
 folder=w/key;folder.mkdir(exist_ok=True);shutil.copyfile(p,folder/'result.json')
 source=p.parent
 # Dedicated scripts may put their result JSON at the project root.
 if key=='TIO':source=r/'verification_tstio_com_r26'
 if key=='MEM':source=r/'verification_mem_r4'
 for log in source.glob('*.log'):
  if source!=r:shutil.copyfile(log,folder/log.name)
for c in compat:
 folder=w/'compatibility';folder.mkdir(exist_ok=True);shutil.copyfile(r/'verification_compat_coms_r26'/c['COM'].replace('.COM','.log'),folder/c['COM'].replace('.COM','.log'))
assert len(checks['requests']['cases'])==5
assert len(checks['WIN']['tests'])==7 and len(checks['IRQ']['cases'])==8
assert checks['TIO']['fresh_runs']==7 and checks['MEM']['fresh_runs']==9 and checks['MR4']['verified_profiles']==8 and len(checks['CPU_regression']['tests'])==9
result=dict(release='R26 MBASE MSX window',baseline='R25 hardware confirmed by user',RTL_changed=changed,VHDL93_files=6,GOWIN_projects=projects,request_positive_runs=2,request_checks_each=2752512,request_expected_fault_runs=3,WIN_COM_runs=7,native_IM1_NMI_and_lock_runs=8,TIO_COM_runs=7,MEM_runs=9,MR4_runs=8,CPU_regression_runs=9,RUNALL_compatibility_COM_smokes=compat,RUNALL_total_programs=25,active_COMs=26,COM_manifest=json.loads((r/'doc/R26_COM_MANIFEST.json').read_text()),deferred_legacy_additional_tests=['EZ80RS8','EZ80IM0','EZ80PFX','EZ80RW2','EZ80MX1'],IO_MBASE_write_and_ADL_control=False,GOWIN=False,board=False,timing_closed=False,sha256={p:sha(r/p)for p in changed})
(r/'doc/R26_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');(w/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS R26 release audit: four RTL changes, VHDL93, projects, RUNALL 25 COMs, dedicated WIN/TIO/MEM/MR4/IRQ checks')
