"""R26 movable MSX window. DOS calls only after MBASE=0/Z80/lock."""
from pathlib import Path
import json,hashlib,zlib
r=Path(__file__).resolve().parent
text=(r/'build_data_r3.py').read_text();exec(text[:text.index("label('START')")])
ref([0xc3],'START');label('WINDOW_DATA');emit(0)
W=labels['WINDOW_DATA'];SP=0xc001;SPL=0x050001;cases=[]
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5);ref([0xed,0x73],'SAVED_SPS')
for a,v in [(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:emit(0x3a,a&255,a>>8,0xfe,v);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
gate(0xd8)
for sel,val in [(0xe4,0x26),(0xe5,0xd9)]:gate(sel);emit(0xed,0x78,0xfe,val);ref([0xc2],'NOT_READY')
gate(0xd0)
for n,mb in enumerate([0,0x0e,0x0f,0xff]):
 stage(str(n));payload={};checks=[];code=[]
 def e(*xs):code.extend(xs)
 def lhl(a):e(0x21,*a.to_bytes(3,'little'))
 def capture(a,val):
  dest=0x0a9000+len(checks);e(0x32,*dest.to_bytes(3,'little'));checks.append((dest,a,val))
 def wrread(a,val):
  lhl(a);e(0x3e,val,0x77,0x7e);capture(a,val)
 e(0x31,*SPL.to_bytes(3,'little'),0x3e,mb,0xed,0x6d)
 wrread((mb<<16)|W,0x31)
 lhl(0x1b0000|W);e(0x3e,0xce,0x40,0x77)
 lhl((mb<<16)|W);e(0x7e);capture((mb<<16)|W,0xce)
 wrread(0x010000|W,0x42)
 wrread(0x07ffff,0x52);wrread(0x080000,0xa6)
 if mb:
  wrread(W,0x69);wrread(0x00ffff,0xb6)
  lhl((mb<<16)|W);e(0x7e);capture((mb<<16)|W,0xce)
 if mb==0xff:
  for off,v in enumerate([0xc3,0,0x88,0x0a]):
   lhl(0x38+off);e(0x3e,v,0x77)
  e(0xff) # ADL RST 38h: three-byte return on SPL, bank-zero vector RAM.
  for i,x in enumerate([0x3e,0x77,0x32,0x11,0x90,0x0a,0xc9]):payload[0x0a8800+i]=x
 e(0x40,0xc3,0,0);stubfix=len(code)-2
 for i,x in enumerate(code):payload[0x0a8000+i]=x
 tail=[0x40,0x3a,W&255,W>>8,0x32,0x10,0x90,0x0a,0x3e,0,0xed,0x6d,0x40,0xc3,0,0]
 for i,x in enumerate(tail):payload[0x0a8700+i]=x
 after='AFTER_'+str(n)
 for a,v in sorted(payload.items()):
  loadpair('HL',a);emit(0x3e,v)
  if a in (0x0a8000+stubfix,0x0a8000+stubfix+1):bytefix.append((len(b)-1,'Z80_STUB',0,a-0x0a8000-stubfix))
  if a in (0x0a870e,0x0a870f):bytefix.append((len(b)-1,after,0,a-0x0a870e))
  indir('HL',True)
 emit(0x31,SP&255,SP>>8,0x5b,0xc3,0,0x80,0x0a)
 label(after);ref([0xed,0x73],'SPS_SNAPSHOT');ref([0xed,0x7b],'SAVED_SPS')
 for dest,a,val in checks:
  loadpair('HL',dest);indir('HL',False);check(val,a)
 readcheck(0x0a9010,0x61)
 if mb==0xff:readcheck(0x0a9011,0x77)
 la('WINDOW_DATA');check(0x61,(mb<<16)|W)
 for i,v in enumerate(SP.to_bytes(2,'little')):la('SPS_SNAPSHOT'+(''if i==0 else'1'));check(v,('SPS_SNAPSHOT',i))
 spcheck(SPL);cases.append(dict(MBASE=mb,checks=checks,Z80_fetch_with_nonzero_MBASE=True))
emit(0x3e,0);sa('WINDOW_DATA');emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('Z80_STUB');emit(0xf3,0x3e,0x61);sa('WINDOW_DATA');emit(0x5b,0xc3,0,0x87,0x0a)
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
footer=text[text.index("label('FAIL')"):text.index('for at,name,off,i in bytefix:')]
footer=footer.replace('EZ80D3 R3','EZ80WIN R26')
footer=footer.replace('emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)','emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)')
exec(footer)
label('MSG_READY');emit(*b'EZ80WIN R26: READY (use /RUN)\r\n$')
label('MSG_NOT_READY');emit(*b'EZ80WIN R26: NOT READY\r\n$')
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,name in fix:b[at:at+2]=labels[name].to_bytes(2,'little')
assert len(b)+0x100<0xb000
name='EZ80WIN'
(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{x:02x}\n'for x in b))
(r/(name+'.asm')).write_text('; R26 resolved byte listing\nORG 0100h\n'+'\n'.join(f'{k} EQU 0{v:04X}h'for k,v in labels.items())+'\n'+'\n'.join(' DEFB '+','.join(f'0{x:02X}h'for x in b[a:a+n])+f' ; {a+256:04X} {c}'for a,n,c in listing)+'\n')
(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.json')).write_text(json.dumps(dict(name=name,version='R26',bytes=len(b),crc32=f'{zlib.crc32(b):08X}',sha256=hashlib.sha256(b).hexdigest(),labels=labels,cases=cases,private_code='0A8000,0A8700,0A8800',private_results='0A9000..0A9011',private_stack='050001',other_writes=['01:WINDOW_DATA','07FFFF','080000','00:WINDOW_DATA and 00FFFF only with nonzero MBASE'],no_MSX_vector_writes=True,private_bank00_RST_vector_write=True,DOS_may_EI=True),indent=2)+'\n')
print(name,len(b),f'{zlib.crc32(b):08X}')
