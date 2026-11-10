from pathlib import Path
import json,sys
irq_stress='--irq' in sys.argv
root=Path(__file__).resolve().parent.parent
source=(root/'hardware_test/build_data_r3.py').read_text()
exec(source[:source.index("label('START')")],globals())
r=root/'sim/ldx_r17';r.mkdir(exist_ok=True)
label('START');emit(0xf3,0xed,0x56,0x31,0,0xf0);gate(0xa5);gate(0x5a);loadpair('SP',0x05a5c3)
scenarios=[]
for pref in [0x40,0x49,0x52,0x5b]:
 long=bool(pref&8);effective=0x03ffff if long else 0xffff
 for idx,index in enumerate(['IX','IY']):
  for pn,pair in enumerate(['BC','DE','HL','IX','IY']):
   read,write={'BC':(7,15),'DE':(23,31),'HL':(39,47)}.get(pair, (55,63) if pair==index else (49,62))
   disp=[-128,-1,0,1,127][(pn+idx+(pref&3))%5]
   base=(effective-disp)&0xffffff if long else 0x030000|((effective-disp)&0xffff)
   for reading in [False,True]:
    for i,v in enumerate([0x78,0x56,0x34]):
     addr=(effective+i)&(0xffffff if long else 0xffff)
     loadpair('HL',addr);emit(0x3e,v);indir('HL',True,pref=0x49 if long else 0x40)
    flags=[0,255,0xc5,0xd7,0x80,1,0x54,0xaa][len(scenarios)%8]
    emit(1,flags,0,0xc5,0xf1)
    loadpair(pair,0xa1b2c3);loadpair(index,base)
    if irq_stress:emit(0xfb)
    emit(pref,0xdd if index=='IX' else 0xfd,read if reading else write,disp&255)
    if irq_stress:emit(0xf3)
    abs_pair(pair,'SNAP',pref=0x49)
    emit(0xf5,0xc1);ref([0xed,0x43],'FLAGS');la('FLAGS');check(flags)
    expected=0x345678 if reading and long else ((base&0xff0000 if pair==index else 0xa10000)|0x5678) if reading else base if pair==index else 0xa1b2c3
    for i in range(3):la('SNAP'+('' if i==0 else str(i)));check((expected>>(8*i))&255)
    abs_pair('SP','SPCAP',pref=0x49)
    for i,v in enumerate([0xc3,0xa5,5]):la('SPCAP'+('' if i==0 else str(i)));check(v)
    if not reading:
     for i in range(3 if long else 2):
      addr=(effective+i)&(0xffffff if long else 0xffff)
      loadpair('HL',addr);indir('HL',False,pref=0x49 if long else 0x40);check((expected>>(8*i))&255,addr)
    scenarios.append(dict(prefix=f'{pref:02X}',index=index,pair=pair,read=reading,base=f'{base:06X}',effective=f'{effective:06X}',disp=disp,flags=f'{flags:02X}'))
gate(0);emit(0x3e,1);sa('STATUS');emit(0x76)
label('FAIL');emit(0x3e,2);sa('STATUS');emit(0x76)
for n,size in [('SNAP',3),('SPCAP',3),('FLAGS',2),('STATUS',1),('DIAG_ACT',1),('DIAG_EXP',1),('DIAG_MEM',1),('DIAG_ADDR0',1),('DIAG_ADDR1',1),('DIAG_ADDR2',1)]:
 label(n);emit(*([0]*size))
 for i in range(1,size):labels[n+str(i)]=labels[n]+i
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)<0xe000-0x100
for ext,data in [('hex','\n'.join(f'{x:02x}' for x in b)+'\n'),('vh',''.join(f'`define X17_{n} 16\'h{v:04x}\n' for n,v in labels.items())+f'`define X17_END 16\'h{255+len(b):04x}\n'),('json',json.dumps(dict(cases=scenarios,bytes=len(b),labels=labels),indent=2)+'\n')]:
 (r/('test'+('_irq' if irq_stress else '')+'.'+ext)).write_text(data)
print('PASS built 80 indexed-pair CPU cases, four suffixes, displacements -128/-1/0/1/127')
