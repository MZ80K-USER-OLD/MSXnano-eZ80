"""Private IM0 peripheral tests. No DOS/BIOS vector writes; DOS may execute EI."""
from pathlib import Path
import json,hashlib,zlib
r=Path(__file__).resolve().parent
text=(r/'build_data_r3.py').read_text();exec(text[:text.index("label('START')")])
MB=14;SP=0xc001;SPL=0x050001
plans=[dict(ctx=0,kind='rst',vec=v,selector=0xe0+v//8) for v in range(0,64,8)]
plans += [dict(ctx=c,kind='rst',vec=v,selector=0xe0+v//8) for c in (1,2) for v in (0,56)]
plans += [dict(ctx=c,kind='call',vec=0,selector=0xe8) for c in range(3)]
plans += [dict(ctx=c,kind='nop',vec=0,selector=sel) for c in range(3) for sel in (0xe9,0xea,0xeb)]
assert len(plans)==24
payload={};ret_prefix={}
def put(a,xs):
 for i,x in enumerate(xs):payload[a+i]=x
for index in range(9):
 target=0x0a9000+index*128;code=[]
 def e(*xs):code.extend(xs)
 e(0x5b,0xed,0x73,0,0x81,0x0a,0x40,0xed,0x73,0x30,0x81)
 e(0xed,0x57,0x3e,0)
 # LD A,I reflects IEF2 in P/V. LD A,0 does not alter that flag.
 branch=target+len(code)+4+2;e(0xe2,*branch.to_bytes(3,'little'),0x3e,1)
 e(0x32,0x11,0x81,0x0a,0x3e,0x80+index,0x32,0x10,0x81,0x0a)
 e(1,0xe7,0xe7,0,0x3e,0xd4,0xed,0x79)
 ret_prefix[target]=target+len(code);e(0,0xed,0x4d)
 put(target,code)
 if index<8:put(0x0f0000+index*8,[0xc3,*target.to_bytes(3,'little')])
def writebytes(data,after=None):
 for a,v in sorted(data.items()):
  loadpair('HL',a);emit(0x3e,v)
  if after and a in (0x0a7009,0x0a700a):bytefix.append((len(b)-1,after,0,a-0x0a7009))
  indir('HL',True)
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5);ref([0xed,0x73],'SAVED_SPS')
for a,v in [(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:
 emit(0x3a,a&255,a>>8,0xfe,v);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
gate(0xc5);emit(0xed,0x78,0xe6,0x80,0xfe,0x80);ref([0xc2],'NOT_READY')
for selector,expected in [(0xca,1),(0xcb,0xfe)]:
 gate(selector);emit(0xed,0x78,0xfe,expected);ref([0xc2],'NOT_READY')
writebytes(payload);gate(0xd8);cases=[]
for index,q in enumerate(plans):
 stage('0123456789ABCDEFGHIJKLMN'[index]);src=int(q['ctx']!=2);mad=int(q['ctx']!=0)
 target=0x0a9400 if q['kind']=='call' else 0x0a9000+(q['vec']//8)*128
 marker=0x88 if q['kind']=='call' else 0x80+q['vec']//8
 native={};start=0x0a8000 if src else 0x0e8200
 def np(a,xs):
  for i,x in enumerate(xs):native[a+i]=x
 # Configure IRQ while DI; EI is followed by one complete NOP before IACK.
 code=[0x5b,1,0xe7,0xe7,0,0x3e,q['selector'],0xed,0x79,0x3e,0xd1,0xed,0x79,0xfb,0]
 ack=start+len(code)
 if q['kind']=='call':code += list(target.to_bytes(3,'little'))
 resume=start+len(code)
 code += [0xed,0x57,0x3e,0]
 branch=start+len(code)+(4 if src else 3)+2
 code += [0xe2,*branch.to_bytes(3,'little')[:3 if src else 2],0x3e,1]
 code += [0x5b,0x32,0x12,0x81,0x0a,0xf3,0x5b,1,0xe7,0xe7,0,0x3e,0xd4,0xed,0x79,0x5b,0xc3,0,0x70,0x0a]
 np(start,code)
 boot=[0x31,*SPL.to_bytes(3,'little'),0x3e,MB,0xed,0x6d]
 if mad:boot += [0xed,0x7d]
 boot += [0xed,0x46,0x5b if src else 0x40,0xc3,*start.to_bytes(3,'little')[:3 if src else 2]]
 np(0x0a6000,boot)
 np(0x0a7000,[0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,0,0])
 for a in [0x0a8100,0x0a8101,0x0a8102,0x0a8110,0x0a8111,0x0a8112,0x0e8130,0x0e8131]:native[a]=0
 native[ret_prefix[target]]=0x5b if mad else 0
 after='AFTER_'+str(index);writebytes(native,after)
 emit(0x31,SP&255,SP>>8,0x5b,0xc3,0,0x60,0x0a)
 label(after);ref([0xed,0x73],'SPS_SNAPSHOT');ref([0xed,0x7b],'SAVED_SPS')
 frame=[];p=SPL
 if q['kind']!='nop':
  for v in resume.to_bytes(3,'little')[:3 if src else 2][::-1]:p-=1;frame.append((p,v))
  if mad:p-=1;frame.append((p,2+src))
  for i,v in enumerate(p.to_bytes(3,'little')):readcheck(0x0a8100+i,v)
  for i,v in enumerate(SP.to_bytes(2,'little')):readcheck(0x0e8130+i,v)
  readcheck(0x0a8110,marker);readcheck(0x0a8111,0)
  for a,v in frame:readcheck(a,v)
 else:
  for a in (0x0a8100,0x0a8101,0x0a8102,0x0a8110):readcheck(a,0)
 readcheck(0x0a8112,0)
 for i,v in enumerate(SP.to_bytes(2,'little')):la('SPS_SNAPSHOT'+('' if i==0 else '1'));check(v,('SPS_SNAPSHOT',i))
 spcheck(SPL)
 cases.append(dict(index=index,stage='0123456789ABCDEFGHIJKLMN'[index],plan=q,ack_pc=ack,resume_pc=resume,frame=frame))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
footer=text[text.index("label('FAIL')"):text.index('for at,name,off,i in bytefix:')]
footer=footer.replace("label('FINISH');emit(0xd5);", "label('FINISH');emit(0xf3,0xed,0x56,0xd5);")
footer=footer.replace("emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)","emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)")
footer=footer.replace('EZ80D3 R3','EZ80IM0 R19');exec(footer)
label('MSG_READY');emit(*b'EZ80IM0 R19: READY (use /RUN)\r\n$')
label('MSG_NOT_READY');emit(*b'EZ80IM0 R19: NOT READY\r\n$')
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert 0x100+len(b)<0xe000,hex(len(b))
name='EZ80IM0';(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{x:02x}\n' for x in b))
(r/(name+'.asm')).write_text('; R19 resolved executable byte listing\nORG 0100h\n'+'\n'.join(f'{n} EQU 0{v:04X}h' for n,v in labels.items())+'\n'+'\n'.join(' DEFB '+','.join(f'0{x:02X}h' for x in b[a:a+n])+f' ; {0x100+a:04X} {c}' for a,n,c in listing)+'\n')
(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n" for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.json')).write_text(json.dumps(dict(name=name,version='R19',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),crc32=f'{zlib.crc32(b):08X}',labels=labels,cases=cases,expected_frame_entries=24,diagnostic_hooks_required=True,DOS_may_EI=True,no_MSX_vector_writes=True,physical_external_peripheral_test=False),indent=2)+'\n')
print(name,len(b),hashlib.sha256(b).hexdigest())
