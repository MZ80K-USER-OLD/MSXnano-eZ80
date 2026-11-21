from pathlib import Path
import json,hashlib,zlib
r=Path(__file__).resolve().parent
text=(r/'build_data_r3.py').read_text();exec(text[:text.index("label('START')")])
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5);ref([0xed,0x73],'SAVED_SPS')
for a,v in[(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:emit(0x3a,a&255,a>>8,0xfe,v);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
gate(0xc5);emit(0xed,0x78,0xe6,0x80,0xfe,0x80);ref([0xc2],'NOT_READY')
gate(0xd8)
for sel,val in[(0xe0,0x22),(0xe1,0xdd)]:gate(sel);emit(0xed,0x78,0xfe,val);ref([0xc2],'NOT_READY')
gate(0xd8);cases=[];progress_labels=[]
for src in(0,1):
 for op in(0x94,0x9c,0xb4,0xbc,0xc2,0xca,0xc3,0xcb):
  for force in(0,1):
   index=len(cases);gate(0xd0);gate(0);ref([0x11],'PROGRESS_'+str(index));progress_labels.append(index);emit(0xfb,0x0e,9,0xcd,5,0,0xf3);gate(0xa5);gate(0x5a);gate(0xd8)
   stage('0123456789ABCDEFGHIJKLMNOPQRSTUV'[index]);pref=(0x40 if src else 0x5b)if force else None;wide=(pref>>3)&1 if pref is not None else src
   output=(op&1)!=0 if op&0x40 else (op&0x20)!=0
   count=3;bc=3 if wide else 0x7a0003;de=0x6600|(0xe6 if op&8 or op&0x40 else 0xe4)
   value=(0x80 if force else 0x31)if output else 0x66^0x5a;f0=0xd7 if force else 0x2a
   hl=0x030000 if op&8 else 0x02ffff;target=hl if wide else 0x0e0000|(hl&65535)
   targets=[(hl+(-i if op&8 else i))&0xffffff if wide else 0x0e0000|((hl+(-i if op&8 else i))&65535)for i in range(count)]
   for t in targets:loadpair('HL',t);emit(0x3e,value if output else value^255);indir('HL',True)
   start=0x0a8000 if src else 0x0e8200;native={};bytefix_start=len(bytefix)
   def put(a,seq):
    for i,v in enumerate(seq):native[a+i]=v
   put(0x0a6000,[0x31,1,0,5,0x3e,14,0xed,0x6d,0xed,0x7e,0x5b if src else 0x40,0xc3,*start.to_bytes(3,'little')[:3 if src else 2]])
   code=[0x5b,1,f0,0xa6,0,0x5b,0xc5,0x5b,0xf1,0x5b,1,*bc.to_bytes(3,'little'),0x5b,0x11,*de.to_bytes(3,'little'),0x5b,0x21,*hl.to_bytes(3,'little')]
   inst=start+len(code)
   if pref is not None:code+=[pref]
   code +=[0xed,op,0x5b,0xed,0x53,10,0x81,0x0a,0x5b,0xed,0x43,0,0x81,0x0a,0x5b,0x22,3,0x81,0x0a,0x5b,0xf5,0x5b,0xd1,0x5b,0xed,0x53,6,0x81,0x0a]
   if output:code +=[0x5b,1,0xe7,0xe7,0,0x3e,0xfa,0xed,0x79,0xed,0x78,0x5b,0x32,9,0x81,0x0a]
   code +=[0x5b,0xc3,0,0x70,0x0a];put(start,code);put(0x0a7000,[0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,0,0])
   after='AFTER_'+str(index)
   for a,v in sorted(native.items()):
    loadpair('HL',a);emit(0x3e,v)
    if a in(0x0a7009,0x0a700a):bytefix.append((len(b)-1,after,0,a-0x0a7009))
    indir('HL',True)
   emit(0x5b,0xc3,0,0x60,0x0a);label(after)
   nextHL=(hl+(-count if op&8 else count))&0xffffff if wide else (hl&0xff0000)|((hl+(-count if op&8 else count))&65535)
   nextde=de if op&0x40 else (de+(-count if op&8 else count))&0xffffff
   expected=[0,0,0 if wide else 0x7a,*nextHL.to_bytes(3,'little'),(f0&0xbd)|0x40|(2 if value&128 else 0),0xa6,0]
   for i,v in enumerate(expected):readcheck(0x0a8100+i,v)
   for i,v in enumerate(nextde.to_bytes(3,'little')):readcheck(0x0a810a+i,v)
   if output:readcheck(0x0a8109,value^0x66)
   else:
    for t in targets:readcheck(t,value)
   spcheck(0x050001)
   cases.append(dict(index=index,op=f'{op:02X}',ADL=src,prefix=pref,BC=bc,DE=de,count=count,data=value,address=f'{target:06X}',instruction=f'{inst:06X}',expected=expected))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
footer=text[text.index("label('FAIL')"):text.index('for at,name,off,i in bytefix:')].replace('EZ80D3 R3','EZ80IOR R22')
footer=footer.replace("label('FINISH');emit(0xd5);","label('FINISH');emit(0xf3,0xed,0x56,0xd5);")
footer=footer.replace("emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)","emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)")
exec(footer);label('MSG_READY');emit(*b'EZ80IOR R22: READY (use /RUN)\r\n$');label('MSG_NOT_READY');emit(*b'EZ80IOR R22: NOT READY\r\n$')
for i in progress_labels:label('PROGRESS_'+str(i));emit(*('CASE '+str(i)+chr(13)+chr(10)+'$').encode())
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)+0x100<0xe000
name='EZ80IOR';(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{v:02x}\n'for v in b));(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.asm')).write_text('ORG 0100h\n'+'\n'.join(f'{n} EQU 0{v:04X}h'for n,v in labels.items())+'\n'+'\n'.join(' DEFB '+','.join(f'0{v:02X}h'for v in b[a:a+n])+f' ; {0x100+a:04X}'for a,n,_ in listing)+'\n')
(r/(name+'.json')).write_text(json.dumps(dict(name=name,version='R22',bytes=len(b),crc32=f'{zlib.crc32(b):08X}',sha256=hashlib.sha256(b).hexdigest(),labels=labels,cases=cases,DOS_may_EI=True,private_IO_loopback='low E4/E5/E6, IORQ suppressed while diagnostics active',physical_external_IO_device_tested=False),indent=2)+'\n');print(name,len(b),f'{zlib.crc32(b):08X}')
