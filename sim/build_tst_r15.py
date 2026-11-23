from pathlib import Path
import json
r=Path(__file__).resolve().parent/'tst_r15';r.mkdir(exist_ok=True)
def andflags(a,b):
 x=a&b
 return (x&0xa8)|(0x40 if x==0 else 0)|0x10|(4 if x.bit_count()%2==0 else 0)
def negflags(a):
 x=(-a)&255
 return (x&0xa8)|(0x40 if x==0 else 0)|(0x10 if a&15 else 0)|(4 if a==128 else 0)|2|(1 if a else 0)
for case in range(5):
 m={};checks=[];p=0;adl=case not in [2,3,4]
 def at(v):
  global p;p=v
 def e(*bs):
  global p
  for b in bs:m[p]=b;p+=1
 def ld(op,v):e(op,*v.to_bytes(3 if adl else 2,'little'))
 def af(a,f):ld(1,(a<<8)|f);e(0xc5,0xf1)
 def state(a,f,mb=0):checks.append(dict(pc=p,acc=a,flags=f,mb=mb,adl=int(adl)))
 at(0);e(0xc3,0,1)
 at(0x100);e(0xf3,0x31,0,0xf0)
 if adl:
  e(1,0xe7,0xe7,0x3e,0xa5,0xed,0x79,0x3e,0x5a,0xed,0x79,0x5b,0xc3,0,0,0x0a)
  at(0x0a0000);ld(0x31,0x050080)
 if case==4:
  e(1,0xe7,0xe7,0x3e,0xa5,0xed,0x79,0x3e,0x5a,0xed,0x79,0xc3,0,0x30)
  at(0x3000)
  for reg in [0,1,2,3,4,5,7]:
   for a in [0,1,0x55,0x80,0x81,0xfe,0xff]:
    b=a^0xa5;af(a,a^0xb7)
    if reg!=7:e(0x06+8*reg,b)
    else:b=a
    e(0xed,0x04+8*reg);state(a,andflags(a,b))
    e(0x78+reg);state(b,andflags(a,b))
  for pref in [None,0x40,0x49,0x52,0x5b]:
   af(0x81,0xff)
   if pref is not None:e(pref)
   e(0xed,0x64,0xa5);state(0x81,andflags(0x81,0xa5))
   e(0x5b,0x21,0,0x48,3);af(0x55,0xff)
   logical=0x034800 if pref in [0x49,0x5b] else 0x4800
   operand=0xa5 if logical>0xffff else 0x3c;m[logical]=operand
   if pref is not None:e(pref)
   e(0xed,0x34);state(0x55,andflags(0x55,operand))
 elif case==0:
  # All A values, every register source, varied pre-flags; check source afterward.
  for reg in [0,1,2,3,4,5,7]:
   for a in range(256):
    b=((a*37)^0xa5)&255
    af(a,((a*19)^0xd7)&255)
    if reg!=7:e(0x06+8*reg,b)
    else:b=a
    f=andflags(a,b);e(0xed,0x04+8*reg);state(a,f)
    e(0x78+reg);state(b,f)
  for a in range(256):
   b=a^0x5a;af(a,a^0xff);e(0xed,0x64,b);state(a,andflags(a,b))
 elif case==1:
  e(0x3e,14,0xed,0x6d)
  for addr in [0x03ffff,0x040000,0x000080,0x1bffff]:
   for pref in [None,0x40,0x49,0x52,0x5b]:
    for a in [0,0xff,0x81,0x55]:
     ld(0x21,addr);af(a,a^0xb3)
     logical=(0x0e0000|(addr&0xffff)) if pref in [0x40,0x52] else addr
     operand=0x3c if pref in [0x40,0x52] else 0xa5
     m[logical]=operand
     if pref is not None:e(pref)
     e(0xed,0x34);state(a,andflags(a,operand),14)
     e(0x7c);state((addr>>8)&255,andflags(a,operand),14)
     e(0x7d);state(addr&255,andflags(a,operand),14)
  e(0x3e,0,0xed,0x6d)
 elif case==2:
  e(0xc3,0,0x30);at(0x3000)
  # Locked ED74 retains NEG; unlocked ED74 is covered by the R25 TSTIO tests.
  for a in range(256):af(a,a^0xff);e(0xed,0x74);state((-a)&255,negflags(a))
 else:
  for a in range(256):
   af(a,a^0xb7);e(0xed,0x04);state(a,a^0xb7)
   e(0xed,0x64);state((-a)&255,negflags(a))
 if adl:e(0x40,0xc3,0,2)
 else:e(0xc3,0,2 if case==2 else 0x7f)
 lines=[f"mem[24'h{a:06x}]=8'h{v:02x};" for a,v in sorted(m.items())]
 for i,j in enumerate(checks):
  lines += [f"epc[{i}]=24'h{j['pc']:06x};",f"eacc[{i}]=8'h{j['acc']:02x};",f"ef[{i}]=8'h{j['flags']:02x};",f"emb[{i}]=8'h{j['mb']:02x};",f"eadl[{i}]={j['adl']};",f"check_a[{i}]=1;check_f[{i}]=1;"]
 lines.append(f'nchecks={len(checks)};')
 (r/f'case{case}.vh').write_text('\n'.join(lines)+'\n')
 (r/f'case{case}.json').write_text(json.dumps(dict(case=case,checks=checks),indent=2)+'\n')
