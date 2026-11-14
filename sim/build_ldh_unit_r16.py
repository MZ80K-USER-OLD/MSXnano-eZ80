from pathlib import Path
import json,sys
irq_stress='--irq' in sys.argv
root=Path(__file__).resolve().parent.parent
source=(root/'hardware_test/build_data_r3.py').read_text()
exec(source[:source.index("label('START')")],globals())
r=root/'sim/ldh_r16';r.mkdir(exist_ok=True)
ops={'BC':(7,15),'DE':(23,31),'HL':(39,47),'IX':(55,63),'IY':(49,62)}
label('START');emit(0xf3,0xed,0x56,0x31,0x00,0xf0);gate(0xa5);gate(0x5a)
scenarios=[]
for pref in [0x40,0x49,0x52,0x5b]:
 long=bool(pref&8);base=0x03ffff if long else 0xffff
 for pair,(read,write) in ops.items():
  for reading in [False,True]:
   for i,v in enumerate([0x78,0x56,0x34]):
    addr=(base+i)&(0xffffff if long else 0xffff)
    loadpair('HL',addr);emit(0x3e,v);indir('HL',True,pref=0x49 if long else 0x40)
   # Flags C5; initialize source, then HL address. HL-as-source is the base itself.
   emit(1,0xc5,0,0xc5,0xf1)
   loadpair(pair,0xa1b2c3);loadpair('HL',base)
   if irq_stress:emit(0xfb)
   emit(pref,0xed,read if reading else write)
   if irq_stress:emit(0xf3)
   abs_pair(pair,'SNAP',pref=0x49)
   emit(0xf5,0xc1);ref([0xed,0x43],'FLAGS')
   la('FLAGS');check(0xc5)
   expected=0x345678 if reading and long else (0x005678 if pair=='HL' else 0xa15678) if reading else base if pair=='HL' else 0xa1b2c3
   for i in range(3):
    la('SNAP'+('' if i==0 else str(i)));check((expected>>(8*i))&255)
   if not reading:
    for i in range(3 if long else 2):
     addr=(base+i)&(0xffffff if long else 0xffff)
     loadpair('HL',addr);indir('HL',False,pref=0x49 if long else 0x40);check((expected>>(8*i))&255,addr)
   scenarios.append(dict(prefix=f'{pref:02X}',pair=pair,read=reading,base=f'{base:06X}'))
gate(0);emit(0x3e,1);sa('STATUS');emit(0x76)
label('FAIL');emit(0x3e,2);sa('STATUS');emit(0x76)
for n,size in [('SNAP',3),('FLAGS',2),('STATUS',1),('DIAG_ACT',1),('DIAG_EXP',1),('DIAG_MEM',1),('DIAG_ADDR0',1),('DIAG_ADDR1',1),('DIAG_ADDR2',1)]:
 label(n);emit(*([0]*size))
 for i in range(1,size):labels[n+str(i)]=labels[n]+i
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)<0xc000-0x100
(r/('test_irq.hex' if irq_stress else 'test.hex')).write_text('\n'.join(f'{x:02x}' for x in b)+'\n')
(r/('test_irq.vh' if irq_stress else 'test.vh')).write_text(''.join(f'`define L16_{n} 16\'h{v:04x}\n' for n,v in labels.items())+f'`define L16_END 16\'h{255+len(b):04x}\n')
(r/('oracle_irq.json' if irq_stress else 'oracle.json')).write_text(json.dumps(dict(cases=scenarios,labels=labels,bytes=len(b)),indent=2)+'\n')
print('PASS built 40 indirect pair CPU cases, all four width prefixes, long carry/short wrap')
