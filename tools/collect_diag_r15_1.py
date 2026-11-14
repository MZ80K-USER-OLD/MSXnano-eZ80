from pathlib import Path
import json,hashlib,zipfile
r=Path(__file__).resolve().parent.parent;w=r/'verification_diag_r15_1'
cases=[('mem',d,p,f) for d,p,f in [(16,0,0),(4,3,0),(16,7,1),(4,3,2)]]+[('tst',d,p,f) for d,p,f in [(16,0,0),(4,7,0),(4,3,1)]]
rows=[]
for k,d,p,f in cases:
 s=(w/f'{k}_d{d}_p{p}_f{f}.log').read_text();assert 'PASS '+k+'_diag_r15_1' in s and 'FATAL' not in s
 if k=='mem' and f:assert 'ADDR=020102 EXP=A2 ACT=A3' in s
 if k=='tst' and not f:assert 'TS36' in s and 'EZ80TS1 P2: PASS' in s
 rows.append(dict(case=[k,d,p,f],output=s))
with zipfile.ZipFile(r.parent/'r15_1-input/MSXnano_T80_eZ80_restart_R15.zip') as z:
 baseline=json.loads(z.read('MSXnano_T80_eZ80_restart_R15/verification_result.json'))
 for n,h in baseline['sha256'].items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
j=dict(series='R15.1 software diagnostics',fresh_diagnostic_runs=7,fault_injection_runs_included=3,FPGA_byte_identical_to_R15=True,original_20_COM_unchanged=True,ordinary_Z80_IRQ_during_DOS=True,BDOS_enables_interrupts=True,DOS_only_with_extensions_locked=True,cases=rows,hardware_freeze_reproduced=False,hardware_root_cause_confirmed=False,GOWIN_run=False,hardware_run=False,scope='real COM + synthesized CPU + bridge/controller + behavioral SDRAM; no routed delay simulation or complete MSX BIOS/DOS',sha256=baseline['sha256'])
(r/'verification_diag_r15_1_result.json').write_text(json.dumps(j,indent=2)+'\n')
print('PASS 7 fresh diagnostic cases (3 injected faults), all FPGA and 20 original COM identical to R15')
