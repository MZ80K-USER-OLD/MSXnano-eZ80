from pathlib import Path
import json
r=Path(__file__).resolve().parent
s=(r/'templates/build_sleep_r20_2.py.txt').read_text()
s=s.replace("plans=[dict(src=src,madl=madl,pref=pref)for src in(0,1)for madl in(0,1)for pref in(None,)]", "plans=[dict(src=src,madl=0,pref=pref)for src in(0,1)for pref in(None,0x40,0x49,0x52,0x5b)]")
s=s.replace("(0xf2,1),(0xf3,0xfe)","(0xce,2),(0xcf,0xfd)")
s=s.replace("0x3e,0xd3,0xed,0x79", "0x3e,0xc0,0xed,0x79")
s=s.replace("readcheck(0x0a8103,0xa7)","readcheck(0x0a8103,0x45)")
s=s.replace("else 0x7e,0xed,0x56", "else 0x7e,0xed,0x5e")
s=s.replace("gate(0xd0);gate(0)","emit(0xed,0x56);gate(0xd0);gate(0)")
s=s.replace("EZ80SL2","EZ80NP6").replace("R20.2","R20.6")
s=s.replace("expected_sleep_entries=4","expected_sleep_entries=0")
s=s.replace("production_wake='RESET only'","production_wake='SLP unsupported: NOP'").replace("test_wake='D3 private diagnostic escape, not IRQ/NMI'","test_wake='No sleep or diagnostic escape'")
exec(compile(s,str(r/'templates/build_sleep_r20_2.py.txt'),'exec'),{'__file__':str(r/'build_nop_r20_6.py')})
p=r/'EZ80NP6.json';m=json.loads(p.read_text());m['expected_NOP_cases']=10;m['IM_preservation_checked_in_unit_test']=True
for c in m['cases']:c['nop_pc']=c.pop('sleep_pc')
p.write_text(json.dumps(m,indent=2)+'\n')
