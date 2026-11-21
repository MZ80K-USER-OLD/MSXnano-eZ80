"""MSX-DOS regression of width-prefix lifetime across terminal CB opcodes."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent
old=(r/'build_io_nop_r23_1.py').read_text()
ns={'__file__':__file__}
exec(compile(old[:old.rindex('exec(compile(s,')],str(r/'build_io_nop_r23_1.py'),'exec'),ns)
s=ns['s']
s=s.replace("plans=[dict(src=src,madl=0,pref=None,op=op)for src in(0,1)for op in(0x84,0x8c,0xa4,0xac)]", "plans=[dict(src=src,madl=0,pref=pref,op=op)for src in(0,1)for pref in(0x40,0x49,0x52,0x5b)for op in(0xdd,0xfd)]")
s=s.replace('(0xf8,0),(0xf9,0xff)','(0xe0,0x24),(0xe1,0xdb)')
s=s.replace('for sel,val in[(0xe0,0x24),(0xe1,0xdb)]:', 'gate(0xd8) # E-page diagnostic selectors require an active diagnostic session\nfor sel,val in[(0xe0,0x24),(0xe1,0xdb)]:')
s=s.replace('0x5b,0x21,0xac,0x68,0x24','0x5b,0x21,0x20,0x68,0x24')
s=s.replace("code +=[0xed,q['op'],0xf3", "code +=[0xcb,q['op'],0x11,0x34,0xab]+([0x12]if src else[])+[0xf3")
s=s.replace('[0xd7,0xa6,0,0x9b,0x57,0x13,0xac,0x68,0x24]', "[0xd7,0xa6,0,0x34,0xab,0x12 if src else 0x13,0x28 if q['op']==0xdd else 0xa0,0x68,0x24]")
s=s.replace('EZ80ION','EZ80DEC').replace('R23.1','R24')
exec(compile(s,str(r/'templates/build_sleep_r20_2.py.txt'),'exec'),{'__file__':__file__})
p=r/'EZ80DEC.json';m=json.loads(p.read_text());m['expected_decode_cases']=16
m['purpose']='Width-prefix lifetime: CB DD/FD followed by default-width LD DE,nn in Z80/ADL'
for c in m['cases']:c['cb_pc']=c.pop('sleep_pc')
p.write_text(json.dumps(m,indent=2)+'\n')
