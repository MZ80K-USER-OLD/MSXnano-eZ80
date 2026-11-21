from pathlib import Path
import json,zlib,hashlib
r=Path(__file__).resolve().parent;text=(r/'build_data_r3.py').read_text();exec(text[:text.index("label('START')")])
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5);ref([0xed,0x73],'SAVED_SPS')
for a,v in[(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:emit(0x3a,a,0,0xfe,v);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
gate(0xc5);emit(0xed,0x78,0xe6,0x80,0xfe,0x80);ref([0xc2],'NOT_READY');gate(0xd8)
for sel,val in[(0xe0,0x23),(0xe1,0xdc)]:gate(sel);emit(0xed,0x78,0xfe,val);ref([0xc2],'NOT_READY')
def progress(n):
 gate(0);ref([0x11],n);emit(0xfb,0x0e,9,0xcd,5,0,0xf3);gate(0xa5);gate(0x5a);gate(0xd8)
def setup():
 emit(1,0x2a,0xa6,0xc5,0xf1)
 loadpair('BC',0x7af6e6);loadpair('DE',0x123456);loadpair('HL',0x789abc)
def capture():
 ref([0x49,0xed,0x43],'SNAP_BC');ref([0x49,0xed,0x53],'SNAP_DE');ref([0x49,0x22],'SNAP_HL')
 emit(0xf5,0xe1);ref([0x22],'SNAP_AF')
def compare(flags):
 for name,value,count in [('SNAP_BC',0x7af6e6,3),('SNAP_DE',0x123456,3),('SNAP_HL',0x789abc,3),('SNAP_AF',0xa600|flags,2)]:
  for j in range(count):
   ref([0x3a],name+str(j));check((value>>(j*8))&255,(name,j))
cases=[];chars='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl'
for pi,pref in enumerate([None,0x40,0x49,0x52,0x5b]):
 progress('PROGRESS_'+str(pi))
 for mask in [0,0xff,0x5a,0x81,0x0f,0xf0,0xaa,0x55]:
  i=len(cases);stage(chars[i]);setup()
  if pref is not None:emit(pref)
  emit(0xed,0x74,mask);capture();result=0x5a&mask
  flags=(result&0xa8)|0x10|(0x40 if result==0 else 0)|(4 if result.bit_count()%2==0 else 0)
  compare(flags);cases.append(dict(index=i,prefix=pref,mask=mask,input=0x5a,flags=flags,kind='TSTIO'))
progress('PROGRESS_5')
for op in [0x84,0x8c,0xa4,0xac,0x94,0x9c,0xb4,0xbc]:
 i=len(cases);stage(chars[i]);setup();emit(0xed,op);capture();compare(0x2a);cases.append(dict(index=i,opcode=op,kind='excluded NOP'))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
footer=text[text.index("label('FAIL')"):text.index('for at,name,off,i in bytefix:')].replace('EZ80D3 R3','EZ80TIO R23')
footer=footer.replace("label('FINISH');emit(0xd5);","label('FINISH');emit(0xf3,0xed,0x56,0xd5);")
footer=footer.replace("emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)","emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)")
exec(footer)
for n,t in [('MSG_READY','EZ80TIO R23: READY (use /RUN)'),('MSG_NOT_READY','EZ80TIO R23: NOT READY')]:label(n);emit(*(t+'\r\n$').encode())
for i in range(6):label('PROGRESS_'+str(i));emit(*(('TSTIO GROUP '+str(i) if i<5 else 'EXCLUDED IO NOP')+'\r\n$').encode())
for name,count in [('SNAP_BC',3),('SNAP_DE',3),('SNAP_HL',3),('SNAP_AF',2)]:
 label(name)
 for j in range(count):labels[name+str(j)]=0x100+len(b);emit(0)
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)+0x100<0xc000
name='EZ80TIO';(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{v:02x}\n'for v in b));(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.asm')).write_text('ORG 0100h\n'+'\n'.join(' DEFB '+','.join(f'0{v:02X}h'for v in b[a:a+16])for a in range(0,len(b),16))+'\n')
(r/(name+'.json')).write_text(json.dumps(dict(name=name,version='R23',bytes=len(b),crc32=f'{zlib.crc32(b):08X}',sha256=hashlib.sha256(b).hexdigest(),labels=labels,cases=cases,DOS_may_EI=True,private_IO_loopback='00E6 returns 5A; physical IORQ suppressed',physical_external_IO_device_tested=False),indent=2)+'\n');print(name,len(b),f'{zlib.crc32(b):08X}')
