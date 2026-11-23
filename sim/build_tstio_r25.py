from pathlib import Path
import json
r=Path(__file__).resolve().parent/'tstio_r25';r.mkdir(exist_ok=True)
def flags(v):return (v&0xa8)|(0x40 if v==0 else 0)|0x10|(4 if v.bit_count()%2==0 else 0)
def negflags(a):
 v=(-a)&255;return(v&0xa8)|(0x40 if v==0 else 0)|(0x10 if a&15 else 0)|(4 if a==128 else 0)|2|(1 if a else 0)
for case in range(7):
 m={};p=0;checks=[];transactions=[];adl=case in [1,4,6]
 def at(v):
  global p;p=v
 def e(*bs):
  global p
  for x in bs:m[p]=x;p+=1
 def ld(op,v,wide=None):
  if wide is None:wide=adl
  e(op,*v.to_bytes(3 if wide else 2,'little'))
 def af(a,f):ld(1,(a<<8)|f);e(0xc5,0xf1)
 at(0);e(0xc3,0,1)
 at(0x38);e(0xed,0x4d)
 at(0x66);e(0xed,0x45)
 at(0x100);e(0xf3,0xed,0x56,0x31,0,0xf0)
 if case!=2:
  e(1,0xe7,0xe7,0x3e,0xa5,0xed,0x79,0x3e,0x5a,0xed,0x79)
 if adl:e(0x5b,0xc3,0,0,0x0a);at(0x0a0000);ld(0x31,0x058000)
 else:e(0xc3,0,0x20);at(0x2000)
 if case==2:
  for a in range(256):
   af(a,a^0xd7);e(0xed,0x74)
   checks.append(dict(pc=p,a=(-a)&255,f=negflags(a),bc=(a<<8)|(a^0xd7),reads=0))
 else:
  masks=[0,1,2,4,8,0xf,0x10,0x55,0x7f,0x80,0x81,0xaa,0xf0,0xfe,0xff]
  if case>=3:masks=[0,0xff,0x80,0x55]
  for pref in [None,0x40,0x49,0x52,0x5b]:
   for port in ([0xe6] if case>=3 else [0,1,0x7f,0x80,0xe6,0xff]):
    for mask in masks:
     a=(port^mask^0x3c)&255;af(a,mask^0xd7)
     bc=0x429a00|port;e(0x5b,1,*bc.to_bytes(3,'little'))
     if case>=3:e(0xfb)
     begin=p
     if pref is not None:e(pref)
     e(0xed,0x74,mask)
     transactions.append(dict(pc=begin,port=port,mask=mask,value=port^0xa5))
     checks.append(dict(pc=p,a=a,f=flags((port^0xa5)&mask),bc=bc,reads=len(transactions)))
     if case>=3:e(0xf3)
 # Terminal fetch checkpoint after the last test; cleanup to legacy mode.
 if adl:e(0x40,0xc3,0,2)
 else:e(0xc3,0,2)
 lines=[f"mem[24'h{k:06x}]=8'h{v:02x};" for k,v in sorted(m.items())]
 for i,c in enumerate(checks):
  for key,width in [('pc',24),('a',8),('f',8),('bc',24)]:lines.append(f"e{key}[{i}]={width}'h{c[key]:0{width//4}x};")
  lines.append(f'ereads[{i}]={c["reads"]};')
 lines.append(f'nchecks={len(checks)};expected_reads={len(transactions)};')
 (r/f'case{case}.vh').write_text('\n'.join(lines)+'\n')
 (r/f'case{case}.json').write_text(json.dumps(dict(case=case,checks=checks,transactions=transactions),indent=2)+'\n')
print('generated TSTIO: 450 cases per mode, plus 256 locked NEG aliases')
