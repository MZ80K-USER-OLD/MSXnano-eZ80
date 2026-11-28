from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
scope=load(R/'verification_scope_r37/result.json');assert scope['FPGA_sha256']=={str(p.relative_to(R)):sha(p) for p in (R/'fpga').rglob('*') if p.is_file()}
unit=load(R/'verification_ir_flags_r37/result.json');assert unit['cases']==10240 and unit['passed']==10240 and unit['failed']==0
fuse=load(R/'fuse_test/doc/R37_FUSE_SUMMARY.json');assert fuse['LD_A_I_R_passed']==64 and fuse['passed']==25232 and not fuse['new_failures_vs_R36']
assert load(R/'fuse_test/results/ldair_r37/result.json')['passed']==64
for x in load(R/'fuse_test/doc/ARCHIVE_RECOVERY.json')['recovered']:
 p=R/'fuse_test/suite'/Path(x['name']).relative_to('ez80_all_fuse_v1');assert sha(p)==x['sha256']
negative=load(R/'verification_ir_com_negative_r37/result.json');assert negative['new_COM_detects_old_bug']
m=load(R/'hardware_test/EZ80IRF.json');assert m['measured_cases']==36 and sha(R/'EZ80IRF.COM')==sha(R/'hardware_test/EZ80IRF.COM')==m['sha256']
normal=[s.split()[0] for s in (R/'RUNALL.BAT').read_text().splitlines() if s.strip()]+['EZ80MX0','EZ80MX1','EZ80MX2','EZ80MA1','EZ80MR4']
stress='EZ80MEM,EZ80MIX,EZ80MAD,EZ80MB,EZ80IRQ,EZ80IM2,EZ80NMI,EZ80MX0,EZ80MX1,EZ80MX2,EZ80MA1,EZ80MR4'.split(',')
rows=[];e=R/'doc/R37_evidence';e.mkdir(exist_ok=True)
for flag,names in [(False,normal),(True,stress)]:
 w=R/'verification_com_r37'/('stress' if flag else '')
 for name in names:
  p=w/(name+'.log');s=p.read_text();assert 'PASS COM_R37' in s and 'status=1' in s,(name,s[-1200:])
  rows.append(dict(COM=name,stress=flag,passed=True,cycles_compared_to_R36=False,COM_self_check=True,SDRAM_WAIT=True,BDOS_EI=True))
  dest=e/'COM'/('stress' if flag else 'normal')/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for flag in [False,True]:
 w=R/'verification_com_r37_irf'/('stress' if flag else '');s=(w/'EZ80IRF.log').read_text();assert 'EZ80IRF R37: PASS' in s and 'PASS COM_R37' in s
 dest=e/'EZ80IRF'/('stress.log' if flag else 'normal.log');dest.parent.mkdir(exist_ok=True);dest.write_text(s)
for folder in ['verification_scope_r37','verification_ir_flags_r37','verification_ir_com_negative_r37']:
 for p in (R/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.json','.log']:
   dest=e/folder/p.relative_to(R/folder);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
result=dict(release='R37',baseline='R36',scope=scope,independent_instruction_cases=10240,FUSE_target_cases=64,FUSE_target_passed=64,FUSE_all=fuse,existing_COM_runs=rows,new_hardware_test=m,new_hardware_test_normal_PASS=True,new_hardware_test_stress_PASS=True,old_R36_expected_failure=negative,physical_timing_closed=False,GOWIN=False,board=False)
(R/'doc/R37_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS R37 release: 10240 independent cases, 64/64 target FUSE, 42 existing COM runs, 2 new COM profiles and old-core negative')
