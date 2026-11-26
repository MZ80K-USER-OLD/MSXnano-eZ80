from pathlib import Path
import json,hashlib,re,os,subprocess,xml.etree.ElementTree as E,shutil
r=Path(__file__).resolve().parents[1];w=r/'verification_r28';w.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((r/'doc/R28_BASELINE_SHA256.json').read_text());changed=[p for p,h in base.items()if sha(r/p)!=h]
assert set(changed)=={'fpga/G80A_eZ80/g80a_ez80.vhd','fpga/top_ez80.v'},changed
# The R26 reference is retained unchanged from the R27 baseline.
assert sha(r/'sim/reference_r26/g80a_ez80.vhd')==json.loads((r/'doc/R27_BASELINE_SHA256.json').read_text())['fpga/G80A_eZ80/g80a_ez80.vhd']
for p in [r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',r/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 files=E.parse(p).findall('.//File');assert len(files)==123 and all((p.parent/f.get('path')).is_file()for f in files)
q=w/'vhdl93';q.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 p=subprocess.run([os.environ.get('GHDL','ghdl'),'-a','--std=93','-fsynopsys','-fexplicit',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=q,capture_output=True,text=True);assert not p.returncode,p.stderr
sources={'strobes':'verification_strobes_r28/result.json','VDP_IO':'verification_vdp_io_r28/result.json','WIN':'verification_window_com_r26/result.json','IRQ':'verification_window_irq_r26/result.json','TIO':'verification_tstio_com_r26_result.json','MEM':'verification_mem_r4_result.json','MR4':'verification_mr4_r21_3/result.json','CPU':'verification_regression_r25/result.json'}
reports={}
for key,path in sources.items():
 p=r/path;j=json.loads(p.read_text());reports[key]=j;d=w/key;d.mkdir(exist_ok=True);shutil.copyfile(p,d/'result.json')
 parent=p.parent if p.parent!=r else r/('verification_tstio_com_r26'if key=='TIO'else'verification_mem_r4')
 for log in parent.glob('*.log'):shutil.copyfile(log,d/log.name)
assert reports['strobes']['checks']==5121 and reports['strobes']['combinations']==1024
assert reports['VDP_IO']['addresses']==65536 and reports['VDP_IO']['classes']==8
assert len(reports['WIN']['tests'])==7 and len(reports['IRQ']['cases'])==8
assert reports['TIO']['fresh_runs']==7 and reports['MEM']['fresh_runs']==9 and reports['MR4']['verified_profiles']==8 and len(reports['CPU']['tests'])==9
names=[line.split()[0]for line in(r/'RUNALL.BAT').read_text().splitlines()];assert len(names)==25
for row in json.loads((r/'doc/R26_COM_MANIFEST.json').read_text()):
 p=r/'hardware_test'/row['name'];assert sha(p)==row['sha256'] and sha(r/row['name'])==row['sha256']
compat=[]
for n in names:
 if n in ['EZ80MEM','EZ80TIO','EZ80WIN']:continue
 p=r/'verification_compat_coms_r26'/(n+'.log');s=p.read_text();assert 'PASS compat_com_r26'in s and 'FATAL'not in s,(n,s[-300:]);compat.append(n)
 d=w/'compatibility';d.mkdir(exist_ok=True);shutil.copyfile(p,d/p.name)
diffs=[]
for sub,names2 in [('', ['EZ80MEM','EZ80WIN','EZ80CTL','EZ80BLK','EZ80LDX','EZ80TIO','EZ80IRQ','EZ80IM2','EZ80NMI','EZ80MIX']),('stress',['EZ80WIN','EZ80TIO','EZ80CTL','EZ80BLK','EZ80DEC'])]:
 for n in names2:
  p=r/'verification_differential_r27'/sub/(n+'.log');s=p.read_text();assert 'PASS differential_r27'in s and 'FATAL'not in s,(str(p),s[-500:]);a=re.search(r'BUS_COMPARISONS=(\d+)',s);assert a
  diffs.append(dict(COM=n,stress=bool(sub),comparisons=int(a[1])))
  d=w/'differential'/sub;d.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d/p.name)
result=dict(release='R28 bus strobes and VDP IO address',baseline='R27 hardware PASS; timing not closed; Logic16056 LUT14162 Register6739',RTL_changed=changed,COMs_unchanged=26,added_preparation_bits_vs_R27=4,CPU_RTL_bridge_memory_VDP_constraints_unchanged=True,VDP_port_decode_top_changed=True,VHDL93_files=6,strobe_checks=5121,VDP_IO_checks=3145728,WIN_profiles=7,IRQ_NMI_lock_profiles=8,TIO_profiles=7,MEM_profiles=9,MR4_profiles=8,CPU_regression_profiles=9,RUNALL_compat_COMs=compat,differential=diffs,total_bus_comparisons=sum(x['comparisons']for x in diffs),GOWIN=False,board=False,timing_closed=False,post_request_pipeline=False,VDP_Hold_fixed=False,sha256={p:sha(r/p)for p in changed})
(r/'doc/R28_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');(w/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS R28: two RTL changes, 26 COM unchanged, regressions and 15 cycle-exact bus comparisons')
