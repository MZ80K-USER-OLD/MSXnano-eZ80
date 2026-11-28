from pathlib import Path
import json,re,hashlib,shutil
R=Path(__file__).resolve().parents[1];W=R/'verification_release_r36';W.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text())
scope=load(R/'verification_scope_r36/result.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert scope['FPGA_sha256']=={str(p.relative_to(R)):sha(p) for p in (R/'fpga').rglob('*') if p.is_file()}
mode=load(R/'verification_mode_byte_r36/result.json');assert mode['cases']==512 and len(mode['rows'])==3
assert all(x['expected_failure_detected'] for x in mode['rows'][1:])
gate=load(R/'verification_frame_gate_r36/result.json');assert gate['cases']==512
capture=load(R/'verification_input_capture_r36/result.json');assert sum(x['checks'] for x in capture['rows'])==32848
width=load(R/'verification_decode_width_r24/result.json');assert width['cases']==64 and len(width['profiles'])==2
normal=[s.split()[0] for s in (R/'RUNALL.BAT').read_text().splitlines() if s.strip()]+['EZ80MX0','EZ80MX1','EZ80MX2','EZ80MA1','EZ80MR4']
stress='EZ80MEM,EZ80MIX,EZ80MAD,EZ80MB,EZ80IRQ,EZ80IM2,EZ80NMI,EZ80MX0,EZ80MX1,EZ80MX2,EZ80MA1,EZ80MR4'.split(',')
assert len(normal)==30 and len(stress)==12
rows=[]
for flag,names in [(False,normal),(True,stress)]:
 w=R/'verification_differential_r36'/('stress' if flag else '')
 name='result_'+('_'.join(names) if flag else 'all')+'.json';manifest=load(w/name)
 assert all(x['passed'] for x in manifest['cases'])
 assert [x['COM'] for x in manifest['cases']]==names
 for n in names:
  p=w/(n+'.log');s=p.read_text();assert 'PASS differential_r27' in s,(n,s[-1000:])
  a=re.search(r'BUS_COMPARISONS=(\d+)',s);b=re.search(r'R36_INPUT_COVERAGE captures=(\d+)',s);assert a and b
  row=next(x for x in manifest['cases'] if x['COM']==n);assert row['sha256']==sha(R/'hardware_test'/(n+'.COM'))
  rows.append(dict(COM=n,stress=flag,CPU_DIV=4,PHASE=3 if flag else 0,CEN_pauses=flag,comparisons=int(a[1]),captures=int(b[1])))
evidence=R/'doc/R36_evidence';evidence.mkdir(exist_ok=True)
for folder in ['verification_scope_r36','verification_mode_byte_r36','verification_frame_gate_r36','verification_input_capture_r36','verification_decode_width_r24','verification_differential_r36']:
 for p in (R/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.json','.log']:
   dest=evidence/folder/p.relative_to(R/folder);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
result=dict(release='R36',baseline='R33',change='Remove frame-header upper-7-bit validation/tag only; keep wrapper input capture',scope=scope,mode_cases=512,mode_negative_controls=2,context_gate_cases=512,input_capture_cases=32848,width_cases=64,differential=rows,total_comparisons=sum(x['comparisons'] for x in rows),COMs_unchanged=30,RUNALL_unchanged=True,GOWIN=False,board=False,timing_closed=False)
(R/'doc/R36_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS R36 release',len(rows),'COM runs;',result['total_comparisons'],'half-clock comparisons')
