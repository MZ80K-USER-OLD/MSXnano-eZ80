from pathlib import Path
import json
r=Path(__file__).resolve().parent/'ldx_adl_irq_r17';r.mkdir(exist_ok=True)
m={};checks=[];p=0

def at(n):
 global p;p=n

def e(*v):
 global p
 for x in v:m[p]=x;p+=1

def ld(pair,v):
 op={'BC':[1],'DE':[0x11],'HL':[0x21],'IX':[0xdd,0x21],'IY':[0xfd,0x21],'SP':[0x31]}[pair];e(*op,*v.to_bytes(3,'little'))

def state(a=None,f=None):checks.append(dict(pc=p,a=a,f=f))

at(0);e(0xc3,0,1)
at(0x100);e(0xf3,0x31,0,0xf0,1,0xe7,0xe7,0x3e,0xa5,0xed,0x79,0x3e,0x5a,0xed,0x79,0x5b,0xc3,0,0,0x0a)
at(0x0a0000);ld('SP',0x050080);e(0x3e,14,0xed,0x6d,0xed,0x56)
operations=[]
for pref in [0x40,0x5b]:
 long=bool(pref&8);effective=0x03ffff if long else 0x0effff
 for idx,index in enumerate(['IX','IY']):
  for pn,pair in enumerate(['BC','DE','HL','IX','IY']):
   read,write={'BC':(7,15),'DE':(23,31),'HL':(39,47)}.get(pair,(55,63) if pair==index else (49,62))
   disp=[-128,-1,0,1,127][(pn+idx)%5]
   base=(effective-disp)&0xffffff if long else 0x030000|((0xffff-disp)&0xffff)
   for reading in [False,True]:
    # Initialize data with ordinary ADL absolute stores before this transfer.
    for i,v in enumerate([0x78,0x56,0x34]):
     addr=(effective+i)&0xffffff if long else 0x0e0000|((0xffff+i)&0xffff)
     e(0x3e,v,0x32,*addr.to_bytes(3,'little'))
    f=[0,255,0xc5,0xd7,0x80,1,0x54,0xaa][len(operations)%8]
    ld('BC',f);e(0xc5,0xf1);ld(pair,0xa1b2c3);ld(index,base)
    e(0xfb,pref,0xdd if index=='IX' else 0xfd,read if reading else write,disp&255);state(f=f);e(0xf3)
    op={'BC':[0xed,0x43],'DE':[0xed,0x53],'HL':[0x22],'IX':[0xdd,0x22],'IY':[0xfd,0x22]}[pair]
    e(*op,0,0x90,0x0a)
    expected=0x345678 if reading and long else ((base&0xff0000 if pair==index else 0xa10000)|0x5678) if reading else base if pair==index else 0xa1b2c3
    for i in range(3):e(0x3a,i,0x90,0x0a);state((expected>>(8*i))&255)
    if not reading:
     for i in range(3 if long else 2):
      addr=(effective+i)&0xffffff if long else 0x0e0000|((0xffff+i)&0xffff)
      e(0x3a,*addr.to_bytes(3,'little'));state((expected>>(8*i))&255)
    operations.append(dict(pair=pair,index=index,prefix=f'{pref:02x}',read=reading,disp=disp))
e(0xc3,0,0x80,0x0a)
at(0x0a8000);e(0x76)
at(0x38);e(0xc3,0,0,0x0b);at(0x0b0000);e(0xed,0x4d)
at(0x66);e(0xc3,0,0x10,0x0b);at(0x0b1000);e(0xed,0x45)
lines=[f"mem[24'h{a:06x}]=8'h{v:02x};" for a,v in sorted(m.items())]
for i,c in enumerate(checks):
 lines.extend([f"epc[{i}]=24'h{c['pc']:06x};",f"eacc[{i}]=8'h{(c['a'] or 0):02x};",f"ef[{i}]=8'h{(c['f'] or 0):02x};",f"check_a[{i}]={int(c['a'] is not None)};",f"check_f[{i}]={int(c['f'] is not None)};"])
lines.append(f'nchecks={len(checks)};')
(r/'test.vh').write_text('\n'.join(lines)+'\n');(r/'oracle.json').write_text(json.dumps(dict(checks=checks,operations=operations),indent=2)+'\n');print('PASS built 40 native ADL indexed transfers with IRQ/NMI boundaries')
