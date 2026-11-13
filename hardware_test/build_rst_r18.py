"""EZ80RS8: private vector RST test; no writes to MSX/DOS restart vectors."""
from pathlib import Path
import json,hashlib,zlib
r=Path(__file__).resolve().parent
# Share the established byte emitter and first-mismatch diagnostic formatter.
text=(r/'build_data_r3.py').read_text();exec(text[:text.index("label('START')")])
plans=[dict(src=s,dst=d,vec=v,madl=(v//8)%2,kind='suffix') for s in (0,1) for d in (0,1) for v in range(0,64,8)]
plans += [dict(src=s,dst=s,vec=v,madl=1,kind='bare') for s in (0,1) for v in (0,56)]
assert len(plans)==36
MB=14;SP=0xc001;SPL=0x050001;A=0xa6;F=0xd7
payload={}
def put(a,xs):
 for i,x in enumerate(xs):payload[a+i]=x
# Long RSTs read bank-zero vectors through the existing private diagnostic window.
# The loader writes 0F:nnnn, never the DOS/MSX vectors at 00:nnnn.
for dst in (0,1):
 for index,v in enumerate(range(0,64,8)):
  target=(0x0a9000 if dst else 0x0e9000)+index*64
  put((0x0f0000 if dst else 0x0e0000)+v,[0xc3,*target.to_bytes(3,'little')[:3 if dst else 2]])
  code=[0x5b,0xed,0x73,0,0x81,0x0a,0x40,0xed,0x73,0x30,0x81,0xf5,0xc1,
        0x5b,0xed,0x43,0x10,0x81,0x0a,0x3e,0x80+index+16*dst,
        0x5b,0x32,0x20,0x81,0x0a,0xc5,0xf1,0x5b if dst else 0x49,0xc9]
  assert len(code)<64;put(target,code)
def writebytes(m):
 for a,v in sorted(m.items()):loadpair('HL',a);emit(0x3e,v);indir('HL',True)
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5)
ref([0xed,0x73],'SAVED_SPS')
# /RUN is required. No private-memory writes on READY / unsupported paths.
for a,v in [(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:
 emit(0x3a,a&255,a>>8,0xfe,v);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
gate(0xc5);emit(0xed,0x78,0xe6,0x88,0xfe,0x88);ref([0xc2],'NOT_READY')
writebytes(payload)
# Arm read-only vector redirection, with the real IRQ line masked. DI also stays set.
gate(0xd8)
cases=[]
for index,q in enumerate(plans):
 stage('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[index]);src=q['src'];dst=q['dst'];vec=q['vec'];mad=q['madl']
 start=0x0a8000 if src else 0x0e8200
 rst=([((0x40,0x49),(0x52,0x5b))[src][dst]] if q['kind']=='suffix' else [])+[0xc7+vec]
 retpc=start+len(rst)
 frame=[]
 if dst==0:
  frame += [(0x0ec000,(retpc>>8)&255),(0x0ebfff,retpc&255)]
  if src:frame.append((0x050000,retpc>>16))
  frame.append((SPL-1-src,2+src));sps=SP-2;spl=SPL-1-src
 else:
  p=SPL
  for v in retpc.to_bytes(3,'little')[:3 if src else 2][::-1]:p-=1;frame.append((p,v))
  p-=1;frame.append((p,2+src));sps=SP;spl=p
 # Populate private native code and a cleanup jump patched to this host continuation.
 native={}
 def nativeput(a,xs):
  for i,x in enumerate(xs):native[a+i]=x
 nativeput(start,rst+[0x5b,0xc3,0,0x70,0x0a])
 boot=[0x31,*SPL.to_bytes(3,'little'),0x3e,MB,0xed,0x6d]
 if mad:boot += [0xed,0x7d]
 boot += [1,F,A,0,0xc5,0xf1,0x5b if src else 0x40,0xc3,*start.to_bytes(3,'little')[:3 if src else 2]]
 nativeput(0x0a6000,boot)
 # R3 bytefix patches the host-return address bytes in the loader after all labels resolve.
 after='AFTER_'+str(index)
 cleanup=[0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,0,0]
 nativeput(0x0a7000,cleanup)
 for a,v in sorted(native.items()):
  loadpair('HL',a);emit(0x3e,v)
  if a in (0x0a7009,0x0a700a):bytefix.append((len(b)-1,after,0,a-0x0a7009))
  indir('HL',True)
 emit(0x31,SP&255,SP>>8,0x5b,0xc3,0,0x60,0x0a)
 label(after);ref([0xed,0x73],'SPS_SNAPSHOT');ref([0xed,0x7b],'SAVED_SPS')
 # Every memory mismatch reports its logical address, expected byte and actual byte.
 for i,v in enumerate(spl.to_bytes(3,'little')):readcheck(0x0a8100+i,v)
 for i,v in enumerate(sps.to_bytes(2,'little')):readcheck(0x0e8130+i,v)
 readcheck(0x0a8110,F);readcheck(0x0a8111,A);readcheck(0x0a8120,0x80+vec//8+16*dst)
 for a,v in frame:readcheck(a,v)
 # Return pointers, captured before restoring the DOS stack.
 for i,v in enumerate(SP.to_bytes(2,'little')):la('SPS_SNAPSHOT'+('' if i==0 else '1'));check(v,('SPS_SNAPSHOT',i))
 ref([0x49,0xed,0x73],'SP_SNAPSHOT')
 for i,v in enumerate(SPL.to_bytes(3,'little')):la('SP_SNAPSHOT'+('' if i==0 else str(i)));check(v,('SP_SNAPSHOT',i))
 cases.append(dict(index=index,stage='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[index],plan=q,return_pc=retpc,entry_SPS=sps,entry_SPL=spl,frame=frame))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
footer=text[text.index("label('FAIL')"):text.index('for at,name,off,i in bytefix:')]
footer=footer.replace("emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)","emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)")
footer=footer.replace('EZ80D3 R3','EZ80RS8 R18').replace('UNSUPPORTED','UNSUPPORTED')
exec(footer)
label('MSG_READY');emit(*b'EZ80RS8 R18: READY (use /RUN)\r\n$')
label('MSG_NOT_READY');emit(*b'EZ80RS8 R18: NOT READY\r\n$')
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert 0x100+len(b)<0xe000,hex(len(b))
name='EZ80RS8';(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{x:02x}\n' for x in b))
(r/(name+'.asm')).write_text('; R18 resolved executable byte listing\nORG 0100h\n'+'\n'.join(f'{n} EQU 0{v:04X}h' for n,v in labels.items())+'\n'+'\n'.join(' DEFB '+','.join(f'0{x:02X}h' for x in b[a:a+n])+f' ; {0x100+a:04X} {c}' for a,n,c in listing)+'\n')
(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n" for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.json')).write_text(json.dumps(dict(name=name,version='R18',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),crc32=f'{zlib.crc32(b):08X}',labels=labels,cases=cases,required_feature_mask='8800',diagnostic_hooks_required=True,private_vector_window='00:0000..007F read/fetch redirected to 0F:0000..007F',no_MSX_vector_writes=True,SPS=SP,SPL=SPL,MBASE=MB,DOS_may_EI=True,checks='entry SP/SPL, F/A, unique vector marker, exact frame memory bytes and final SPL',not_tested=['ADL IM0','noncanonical full suffixes','real MSX interrupt handler','SLP','reserved-opcode semantics']),indent=2)+'\n')
print(name,len(b),hashlib.sha256(b).hexdigest())
