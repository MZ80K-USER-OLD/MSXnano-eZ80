"""R20 reset-only SLP, diagnostic-only test escape. No DOS calls while unlocked."""
from pathlib import Path
import json,hashlib,zlib
r=Path(__file__).resolve().parent
text=(r/'build_data_r3.py').read_text();exec(text[:text.index("label('START')")])
SP=0xc001;SPL=0x050001
plans=[dict(src=src,madl=madl,pref=pref)for src in(0,1)for madl in(0,1)for pref in(None,)]
def writebytes(data,after=None):
 for a,v in sorted(data.items()):
  loadpair('HL',a);emit(0x3e,v)
  if after and a in(0x0a7009,0x0a700a):bytefix.append((len(b)-1,after,0,a-0x0a7009))
  indir('HL',True)
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5);ref([0xed,0x73],'SAVED_SPS')
for a,v in[(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:emit(0x3a,a&255,a>>8,0xfe,v);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
gate(0xc5);emit(0xed,0x78,0xe6,0x80,0xfe,0x80);ref([0xc2],'NOT_READY')
for sel,val in[(0xf2,1),(0xf3,0xfe)]:gate(sel);emit(0xed,0x78,0xfe,val);ref([0xc2],'NOT_READY')
gate(0xd8);cases=[];progress_labels=[]
def progress(index):
 gate(0xd0);gate(0)
 msg='PROGRESS_'+str(index);progress_labels.append((msg,index));ref([0x11],msg)
 emit(0xfb,0x0e,9,0xcd,5,0,0xf3)
 gate(0xa5);gate(0x5a);gate(0xd8)

for index,q in enumerate(plans):
 progress(index);stage('0123456789ABCDEFGHIJ'[index]);src=q['src'];madl=q['madl'];pref=q['pref'];start=0x0a8000 if src else 0x0e8200
 native={0x0a8100:0,0x0a8101:0,0x0a8102:0,0x0a8103:0}
 def np(a,xs):
  for i,x in enumerate(xs):native[a+i]=x
 # Preserve IM1, AF and both stacks across SLP. MADL=1 cases keep INT pending
 # across EI; [width] ED76, then DI immediately after the diagnostic escape.
 boot=[0x31,*SPL.to_bytes(3,'little'),0x3e,14,0xed,0x6d,0xed,0x7d if madl else 0x7e,0xed,0x56,0x5b if src else 0x40,0xc3,*start.to_bytes(3,'little')[:3 if src else 2]]
 np(0x0a6000,boot)
 code=[0x5b,1,0xe7,0xe7,0,0x3e,0xd3,0xed,0x79]
 if madl:code +=[0x3e,0xd1,0xed,0x79]
 # Load AF last, after OUT instructions. LIL push/pop use the private SPL.
 code +=[0x5b,1,0xd7,0xa6,0,0x5b,0xc5,0x5b,0xf1]
 if madl:code +=[0xfb]
 sleep_pc=start+len(code)+(int(pref is not None))
 if pref is not None:code +=[pref]
 code +=[0xed,0x76,0xf3,0x5b,0xf5,0x5b,0xe1,0x5b,0x22,0,0x81,0x0a]
 code +=[0x5b,1,0xe7,0xe7,0,0xed,0x78,0x5b,0x32,3,0x81,0x0a,0x3e,0xd4,0xed,0x79,0x5b,0xc3,0,0x70,0x0a]
 np(start,code);np(0x0a7000,[0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,0,0])
 after='AFTER_'+str(index);writebytes(native,after);emit(0x31,SP&255,SP>>8,0x5b,0xc3,0,0x60,0x0a)
 label(after);ref([0xed,0x73],'SPS_SNAPSHOT');ref([0xed,0x7b],'SAVED_SPS')
 readcheck(0x0a8100,0xd7);readcheck(0x0a8101,0xa6);readcheck(0x0a8103,0xa7)
 for i,v in enumerate(SP.to_bytes(2,'little')):la('SPS_SNAPSHOT'+(''if i==0 else'1'));check(v,('SPS_SNAPSHOT',i))
 spcheck(SPL);cases.append(dict(index=index,stage='0123456789ABCDEFGHIJ'[index],plan=q,sleep_pc=sleep_pc,return_pc=sleep_pc+2))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
footer=text[text.index("label('FAIL')"):text.index('for at,name,off,i in bytefix:')]
footer=footer.replace("label('FINISH');emit(0xd5);","label('FINISH');emit(0xf3,0xed,0x56,0xd5);")
footer=footer.replace("emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)","emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)")
footer=footer.replace('EZ80D3 R3','EZ80SL2 R20.2');exec(footer)
label('MSG_READY');emit(*b'EZ80SL2 R20.2: READY (use /RUN)\r\n$')
label('MSG_NOT_READY');emit(*b'EZ80SL2 R20.2: NOT READY\r\n$')
for msg,index in progress_labels:label(msg);emit(*('CASE '+str(index)+chr(13)+chr(10)+'$').encode())
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)+0x100<0xe000
name='EZ80SL2';(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{x:02x}\n'for x in b))
(r/(name+'.asm')).write_text('; R20 resolved executable byte listing\nORG 0100h\n'+'\n'.join(f'{n} EQU 0{v:04X}h'for n,v in labels.items())+'\n'+'\n'.join(' DEFB '+','.join(f'0{x:02X}h'for x in b[a:a+n])+f' ; {0x100+a:04X} {c}'for a,n,c in listing)+'\n')
(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.json')).write_text(json.dumps(dict(name=name,version='R20.2',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),crc32=f'{zlib.crc32(b):08X}',labels=labels,cases=cases,expected_frame_entries=0,expected_sleep_entries=4,production_wake='RESET only',test_wake='D3 private diagnostic escape, not IRQ/NMI',expected_progress_prints=len(plans),DOS_may_EI=True,no_MSX_vector_writes=True),indent=2)+'\n');print(name,len(b),f'{zlib.crc32(b):08X}')
