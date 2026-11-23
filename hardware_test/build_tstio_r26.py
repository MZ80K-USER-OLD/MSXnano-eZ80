"""Build MSX-DOS TSTIO test; reuse the established guarded DOS/ADL harness."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent
s=(r/'templates/build_sleep_r20_2.py.txt').read_text()
s=s.replace("plans=[dict(src=src,madl=madl,pref=pref)for src in(0,1)for madl in(0,1)for pref in(None,)]", "plans=[dict(src=src,madl=0,pref=pref)for src in(0,1)for pref in(None,0x40,0x49,0x52,0x5b)]\nmasks=[0,0xff,0x55,0xaa,0x0f,0xf0,0x80,0x81,0x5a,0xa5]\ndef andflags(v):return(v&0xa8)|(0x40 if v==0 else 0)|0x10|(4 if v.bit_count()%2==0 else 0)")
s=s.replace('for sel,val in[(0xf2,1),(0xf3,0xfe)]:','gate(0xd8)\nfor sel,val in[(0xe2,0x25),(0xe3,0xda)]:')
s=s.replace('sleep_pc=start+len(code)+(int(pref is not None))','code +=[0x5b,1,0xe6,0x9a,0x42,0x5b,0x11,0x9b,0x57,0x13]\n sleep_pc=start+len(code)+(int(pref is not None))')
s=s.replace('code +=[0xed,0x76,0xf3,0x5b,0xf5', "code +=[0xed,0x74,masks[index],0xf3,0x5b,0xed,0x43,4,0x81,0x0a,0x5b,0xed,0x53,7,0x81,0x0a,0x5b,0xf5")
s=s.replace('readcheck(0x0a8100,0xd7);readcheck(0x0a8101,0xa6);readcheck(0x0a8103,0xa7)', '''readcheck(0x0a8100,andflags(0x5a & masks[index]));readcheck(0x0a8101,0xa6);readcheck(0x0a8103,0xa7)
 for off,val in enumerate([0xe6,0x9a,0x42,0x9b,0x57,0x13],4):readcheck(0x0a8100+off,val)''')
s=s.replace('0x3e,0xd3,0xed,0x79','0x3e,0xc0,0xed,0x79')
s=s.replace('readcheck(0x0a8103,0xa7)','readcheck(0x0a8103,0x45)')
s=s.replace('return_pc=sleep_pc+2','return_pc=sleep_pc+3')
s=s.replace('EZ80SL2','EZ80TIO').replace('R20.2','R25').replace('; R20 resolved executable byte listing','; R25 TSTIO resolved executable byte listing')
s=s.replace('expected_sleep_entries=4','expected_sleep_entries=0').replace("production_wake='RESET only'","production_wake='TSTIO flags-only I/O read'").replace("test_wake='D3 private diagnostic escape, not IRQ/NMI'","test_wake='No sleep or escape used'")
# R26: short source code lives in MSX RAM, not hidden private bank 0E.
s=s.replace('start=0x0a8000 if src else 0x0e8200','start=0x0a8000 if src else 0x008200').replace('0x3e,14,0xed,0x6d','0x3e,0,0xed,0x6d').replace('R25','R26')
ns={'__file__':__file__}
exec(compile(s,str(r/'templates/build_sleep_r20_2.py.txt'),'exec'),ns)
masks=ns['masks'];andflags=ns['andflags']
p=r/'EZ80TIO.json';m=json.loads(p.read_text());m['purpose']='R26 TSTIO: port 00E6, DIAG value 5A; Z80/ADL + all widths, A/BC/DE and both stacks preserved'
m.pop('production_wake',None);m.pop('test_wake',None);m.pop('expected_sleep_entries',None)
m['feature_id']={'E2':'25','E3':'DA'};m['masks']=masks;m['expected_tstio_reads']=10
for i,c in enumerate(m['cases']):c['tstio_pc']=c.pop('sleep_pc');c['mask']=masks[i];c['expected_flags']=andflags(0x5a&masks[i])
p.write_text(json.dumps(m,indent=2)+'\n')
