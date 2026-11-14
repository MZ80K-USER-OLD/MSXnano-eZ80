"""Width/indexed-CB regression: private RAM/vectors; no DOS calls while extended."""
from pathlib import Path
import json,hashlib,zlib
r=Path(__file__).resolve().parent
text=(r/'build_data_r3.py').read_text();exec(text[:text.index("label('START')")])
MB=14;SP=0xc001;SPL=0x050001
plans=[dict(src=src,iy=iy,pref=pref,irq=irq) for src in (0,1) for iy in (0,1) for pref in (0x40,0x49,0x52,0x5b) for irq in (0,1)]
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
for sel,val in [(0xcc,1),(0xcd,0xfe)]:gate(sel);emit(0xed,0x78,0xfe,val);ref([0xc2],'NOT_READY')
handler=[0x5b,0xed,0x73,0,0x81,0x0a,1,0xe7,0xe7,0,0x3e,0xd4,0xed,0x79,0x5b,0xed,0x4d]
writebytes({**{0x0f0038+i:v for i,v in enumerate([0xc3,0,0x90,0x0a])},**{0x0a9000+i:v for i,v in enumerate(handler)}})
gate(0xd8);cases=[]
for index,q in enumerate(plans):
 stage('0123456789ABCDEFGHIJKLMNOPQRSTUV'[index]);src=q['src'];iy=q['iy'];pref=q['pref'];irq=q['irq']
 long=bool(pref&8);target=(0x03ffff if iy else 0x030000) if long else (0x0effff if iy else 0x0e0000)
 alias=(0x0effff if iy else 0x0e0000) if long else (0x03ffff if iy else 0x030000)
 value=0x73 if iy else 0x31;expected=0x71 if iy else 0x35
 start=0x0a8000 if src else 0x0e8200;native={target:value,alias:0xaa,0x0a8100:0,0x0a8101:0,0x0a8102:0}
 def np(a,xs):
  for i,x in enumerate(xs):native[a+i]=x
 boot=[0x31,*SPL.to_bytes(3,'little'),0x3e,MB,0xed,0x6d,0xed,0x7d,0xed,0x56,0xdd,0x21,0xff,0xff,2,0xfd,0x21,0,0,4,0x5b if src else 0x40,0xc3,*start.to_bytes(3,'little')[:3 if src else 2]]
 np(0x0a6000,boot)
 code=[0x5b,1,0xe7,0xe7,0,0x3e,0xd1,0xed,0x79,0xfb] if irq else []
 code += [pref,0xfd if iy else 0xdd,0xcb,0xff if iy else 1,0x8e if iy else 0xd6]
 resume=start+len(code)
 code += [0x11,0x34,0xab]+([0x12] if src else [])
 code += [0x5b,0xed,0x53,0x20,0x81,0x0a,0xf3,0x5b,1,0xe7,0xe7,0,0x3e,0xd4,0xed,0x79,0x5b,0xc3,0,0x70,0x0a]
 np(start,code);np(0x0a7000,[0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,0,0])
 after='AFTER_'+str(index);writebytes(native,after)
 emit(0x31,SP&255,SP>>8,0x5b,0xc3,0,0x60,0x0a)
 label(after);ref([0xed,0x73],'SPS_SNAPSHOT');ref([0xed,0x7b],'SAVED_SPS')
 readcheck(target,expected);readcheck(alias,0xaa)
 for i,v in enumerate((0x34,0xab)):readcheck(0x0a8120+i,v)
 if src:readcheck(0x0a8122,0x12)
 p=SPL;frame=[]
 if irq:
  for v in resume.to_bytes(3,'little')[:3 if src else 2][::-1]:p-=1;frame.append((p,v))
  p-=1;frame.append((p,2+src))
 for i,v in enumerate((p if irq else 0).to_bytes(3,'little')):readcheck(0x0a8100+i,v)
 for a,v in frame:readcheck(a,v)
 for i,v in enumerate(SP.to_bytes(2,'little')):la('SPS_SNAPSHOT'+('' if i==0 else '1'));check(v,('SPS_SNAPSHOT',i))
 spcheck(SPL)
 cases.append(dict(index=index,stage='0123456789ABCDEFGHIJKLMNOPQRSTUV'[index],plan=q,target=target,expected=expected,alias=alias,return_pc=resume,frame=frame))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
footer=text[text.index("label('FAIL')"):text.index('for at,name,off,i in bytefix:')]
footer=footer.replace("label('FINISH');emit(0xd5);", "label('FINISH');emit(0xf3,0xed,0x56,0xd5);")
footer=footer.replace("emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)","emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)")
footer=footer.replace('EZ80D3 R3','EZ80PFX R19.1');exec(footer)
label('MSG_READY');emit(*b'EZ80PFX R19.1: READY (use /RUN)\r\n$')
label('MSG_NOT_READY');emit(*b'EZ80PFX R19.1: NOT READY\r\n$')
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)+0x100<0xe000,hex(len(b))
name='EZ80PFX';(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{x:02x}\n' for x in b))
(r/(name+'.asm')).write_text('; R19.1 resolved executable byte listing\nORG 0100h\n'+'\n'.join(f'{n} EQU 0{v:04X}h' for n,v in labels.items())+'\n'+'\n'.join(' DEFB '+','.join(f'0{x:02X}h' for x in b[a:a+n])+f' ; {0x100+a:04X} {c}' for a,n,c in listing)+'\n')
(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n" for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.json')).write_text(json.dumps(dict(name=name,version='R19.1',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),crc32=f'{zlib.crc32(b):08X}',labels=labels,cases=cases,expected_frame_entries=16,diagnostic_hooks_required=True,no_MSX_vector_writes=True,DOS_may_EI=True,NMI_boundary_tested_on_board=False),indent=2)+'\n')
print(name,len(b),hashlib.sha256(b).hexdigest())
