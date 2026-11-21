"""Build a guarded MSX-DOS test of the four removed ED opcodes."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent
old=(r/'build_nop_r20_6.py').read_text()
scope={'__file__':__file__}
exec(compile(old[:old.index('exec(compile(s,')],str(r/'build_nop_r20_6.py'),'exec'),scope)
s=scope['s']
s=s.replace("plans=[dict(src=src,madl=0,pref=pref)for src in(0,1)for pref in(None,0x40,0x49,0x52,0x5b)]", "plans=[dict(src=src,madl=0,pref=None,op=op)for src in(0,1)for op in(0x84,0x8c,0xa4,0xac)]")
s=s.replace('(0xce,2),(0xcf,0xfd)','(0xf8,0),(0xf9,0xff)')
s=s.replace('code +=[0x5b,1,0xd7,0xa6,0,0x5b,0xc5,0x5b,0xf1]', 'code +=[0x5b,0x11,0x9b,0x57,0x13,0x5b,0x21,0xac,0x68,0x24,0x5b,1,0xd7,0xa6,0,0x5b,0xc5,0x5b,0xf1]')
s=s.replace('code +=[0xed,0x76,0xf3,0x5b,0xf5', 'code +=[0xed,q[\'op\'],0xf3,0x5b,0xed,0x43,4,0x81,0x0a,0x5b,0xed,0x53,7,0x81,0x0a,0x5b,0x22,10,0x81,0x0a,0x5b,0xf5')
s=s.replace('readcheck(0x0a8100,0xd7);', "\n for off,val in enumerate([0xd7,0xa6,0,0x9b,0x57,0x13,0xac,0x68,0x24],4):readcheck(0x0a8100+off,val)\n readcheck(0x0a8100,0xd7);")
s=s.replace('EZ80NP6','EZ80ION').replace('R20.6','R23.1')
exec(compile(s,str(r/'templates/build_sleep_r20_2.py.txt'),'exec'),{'__file__':__file__})
p=r/'EZ80ION.json';m=json.loads(p.read_text());m['expected_NOP_cases']=8
m['purpose']='Removed INI2/IND2/OUTI2/OUTD2: Z80/ADL, AF/BC/DE/HL and both stacks unchanged'
for c in m['cases']:c['nop_pc']=c.pop('sleep_pc')
p.write_text(json.dumps(m,indent=2)+'\n')
