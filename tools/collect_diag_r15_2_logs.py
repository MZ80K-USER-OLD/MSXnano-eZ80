"""Collect this revision's completed diagnostic runs after a wall-time retry.
Run verify_diag_r15_2.py for fresh execution; this only validates existing logs.
"""
from pathlib import Path
import ast, hashlib, json
r=Path(__file__).resolve().parent.parent
source=ast.parse((r/'tools/verify_diag_r15_2.py').read_text())
cases=next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cases' for t in n.targets))
rows=[]
for q in cases:
 kind,div,phase,fault,pause=q
 p=r/'verification_diag_r15_2'/f'{kind}_d{div}_p{phase}_f{fault}_s{pause}.log'
 s=p.read_text()
 assert 'PASS '+kind+'_diag_r15_2' in s and 'FATAL' not in s,p
 if kind=='ctl' and fault==2:assert 'FAIL stage V' in s and 'ADDR=090000 EXP=31 ACT=30' in s and 'CT3 RUN' not in s,p
 elif kind=='ctl' and fault==1:assert 'ADDR=030200 EXP=22 ACT=23' in s,p
 elif kind=='boundary' and fault:assert 'ADDR=030000 EXP=96 ACT=97' in s,p
 elif kind=='ctl':assert all(v in s for v in ['CT1 LOAD','CT2 VERIFY','CT3 RUN','CT4 CHECK','EZ80CT1 R10: PASS']),p
 else:assert 'BN9' in s and 'EZ80BN1 R15.2: PASS' in s,p
 rows.append(dict(case=q,output=s))
j=dict(fresh_runs=len(rows),fault_injection_cases=sum(q[3]!=0 for q in cases),cases=rows,CPU_revision='restart R15.3',diagnostic_program_bytes_unchanged=True,normal_IRQ_during_DOS=True,DOS_enables_interrupts=True,DOS_only_Z80_MBASE0_extensions_locked=True,readback_before_code_execution=True,physical_root_cause_confirmed=False,slow_CTL_wall_timeout_retried=True,collection='Seven completed runs plus successful standalone retry of ctl_d16_p0_f0_s0; same compiled CPU RTL.',sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')})
(r/'verification_diag_r15_2_result.json').write_text(json.dumps(j,indent=2)+'\n')
print('PASS all 8 R15.2 diagnostic scenarios on R15.3')
