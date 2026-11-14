"""Focused R18 write/read diagnostic: no RST and no ADL code execution."""
from pathlib import Path
import json,hashlib,zlib
r=Path(__file__).resolve().parent
text=(r/'build_data_r3.py').read_text();exec(text[:text.index("label('START')")])
name='EZ80RW2';messages=[];details=[]
def progress(msg):
 key='PROGRESS_'+str(len(messages));messages.append((key,(name+' '+msg+'\r\n$').encode()));ref([0x11],key);ref([0xcd],'PRINT_PROGRESS')
def write(address,value,absolute=False):
 emit(0x3e,value)
 if absolute:emit(0x5b,0x32,*address.to_bytes(3,'little'))
 else:loadpair('HL',address);indir('HL',True)
def read(address,value,absolute=False):
 if absolute:emit(0x5b,0x3a,*address.to_bytes(3,'little'))
 else:loadpair('HL',address);indir('HL',False)
 check(value,address)
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5);ref([0xed,0x73],'SAVED_SPS')
for a,v in [(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:emit(0x3a,a&255,a>>8,0xfe,v);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
gate(0xc5);emit(0xed,0x78,0xe6,0x88,0xfe,0x88);ref([0xc2],'NOT_READY')
progress('START');gate(0)
stage('R')
for v in [0,1,2,3,0x10,0x11,0x30,0x31,0x32,0x33,0x55,0xaa,0xff]:
 emit(0x3e,v,0x47,0xaf,0x78);check(v)
 emit(0x06,v,0xaf,0x78);check(v)
progress('REG PASS');gate(0);stage('F');emit(0x3e,0x31);sa('DIAG_ACT');la('DIAG_ACT');check(0x31)
ref([0x21],'SELF_ACT');la('DIAG_ACT');ref([0xcd],'HEX_BYTE');ref([0x11],'SELF_MESSAGE');ref([0xcd],'PRINT_PROGRESS')
patterns=[0x31,0x33,0,1,2,3,0x55,0xaa,0xff]
# Capture all patterns without DOS or early termination; print the matrix afterwards.
stage('P')
for i,v in enumerate(patterns):
 loadpair('HL',0x0a6000);emit(0x3e,v);indir('HL',True)
 loadpair('HL',0x0a6000);indir('HL',False);sa('PAT_IND_'+str(i))
 emit(0x5b,0x3a,0,0x60,0x0a);sa('PAT_ABS_'+str(i))
gate(0)
for i,v in enumerate(patterns):
 ref([0x21],'TXT_IND_'+str(i));la('PAT_IND_'+str(i));ref([0xcd],'HEX_BYTE')
 ref([0x21],'TXT_ABS_'+str(i));la('PAT_ABS_'+str(i));ref([0xcd],'HEX_BYTE')
ref([0x11],'PATTERN_MESSAGE');ref([0xcd],'PRINT_PROGRESS')

for sid,absolute in [('1',False),('2',True)]:
 stage(sid);progress(sid+(' ABSOLUTE WRITE' if absolute else ' INDIRECT WRITE'))
 for v in patterns:
  write(0x0a6000,v,absolute);read(0x0a6000,v,False);read(0x0a6000,v,True)
 details.append(dict(stage=sid,write='absolute' if absolute else 'indirect',read='indirect+absolute',DOS_between_write_and_read=False,first_expected=0x31))
# Exact private bytes from the R18.1 RS0 first-case loader, including its return jump.
m=json.loads((r/'EZ80RS0.json').read_text());after=m['labels']['AFTER_0'];code={}
for base,xs in [(0x0a6000,[0x31,1,0,5,0x3e,14,0xed,0x6d,1,0xd7,0xa6,0,0xc5,0xf1,0x40,0xc3,0,0x82]),(0x0a7000,[0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,after&255,after>>8]),(0x0e8200,[0x5b,0xc3,0,0x70,0x0a])]:
 for i,v in enumerate(xs):code[base+i]=v
stage('3');progress('3 BLOCK NO DOS')
for a,v in sorted(code.items()):write(a,v)
for a,v in sorted(code.items()):read(a,v)
stage('4');progress('4 BLOCK AFTER DOS')
for a,v in sorted(code.items()):read(a,v)
stage('5');progress('5 CALL CHECKER')
for a,v in sorted(code.items()):loadpair('HL',a);emit(0x3e,v);ref([0xcd],'CHECK_LONG')
stage('6');progress('6 ADDRESS ALIASES')
aliases={0x0a6000:0x31,0x0a6001:0xe1,0x0a6040:0x4c,0x0a7000:0x87,0x0a8000:0x96,0x0e8200:0x69}
for a,v in aliases.items():write(a,v)
for a,v in reversed(list(aliases.items())):read(a,v)
stage('7');progress('7 WINDOW OFF');gate(0xd0)
for a,v in sorted(code.items()):write(a,v)
for a,v in sorted(code.items()):read(a,v)
stage('8');progress('8 WINDOW ON')
for a,v in sorted(code.items()):write(a,v)
progress('8 AFTER DOS')
for a,v in sorted(code.items()):read(a,v)
stage('9');progress('9 ORIGINAL ORDER')
for a,v in sorted(code.items()):loadpair('HL',a);emit(0x3e,v);indir('HL',True)
for a,v in sorted(code.items()):read(a,v)
stage('A');progress('A ORIGINAL AFTER DOS')
for a,v in sorted(code.items()):read(a,v)
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
footer=text[text.index("label('FAIL')"):text.index('for at,name,off,i in bytefix:')]
footer=footer.replace("emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)","emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)")
footer=footer.replace('EZ80D3 R3',name+' R18.2');exec(footer)
label('CHECK_LONG');emit(0x47);indir('HL',False);emit(0xb8,0xc8);sa('DIAG_ACT');emit(0x78);sa('DIAG_EXP');abs_pair('HL','DIAG_ADDR0');emit(0x3e,1);sa('DIAG_MEM');ref([0xed,0x7b],'SAVED_SPS');ref([0xc3],'FAIL')
label('PRINT_PROGRESS');emit(0xf5,0xc5,0xd5,0xe5,0xdd,0xe5,0xfd,0xe5);gate(0);emit(0xfb,0x0e,9,0xcd,5,0,0xf3,0xed,0x56);gate(0xa5);gate(0x5a);gate(0xd8);emit(0xfd,0xe1,0xdd,0xe1,0xe1,0xd1,0xc1,0xf1,0xc9)
for key,msg in messages:label(key);emit(*msg)
label('SELF_MESSAGE');emit(*(name+' SELF EXP=31 ACT=').encode());label('SELF_ACT');emit(*b'00\r\n$')
label('PATTERN_MESSAGE');emit(b'E'[0],*b'Z80RW2 PATTERNS 0A6000\r\n')
for i,v in enumerate(patterns):
 emit(*f'EXP={v:02X} IND='.encode());label('TXT_IND_'+str(i));emit(*b'00 ABS=');label('TXT_ABS_'+str(i));emit(*b'00\r\n')
emit(ord('$'))
for i in range(len(patterns)):label('PAT_IND_'+str(i));emit(0);label('PAT_ABS_'+str(i));emit(0)
label('MSG_READY');emit(*(name+' R18.2: READY (use /RUN)\r\n$').encode());label('MSG_NOT_READY');emit(*(name+' R18.2: NOT READY\r\n$').encode())
for at,n,off,i in bytefix:b[at]=((labels[n]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)+0x100<0x4000
(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{x:02x}\n' for x in b))
(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n" for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.asm')).write_text('; R18.2 resolved byte listing\nORG 0100h\n'+'\n'.join(' DEFB '+','.join(f'0{x:02X}h' for x in b[a:a+n])+f' ; {0x100+a:04X} {c}' for a,n,c in listing)+'\n')
(r/(name+'.json')).write_text(json.dumps(dict(name=name,version='R18.2',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),crc32=f'{zlib.crc32(b):08X}',labels=labels,expected_prints=len(messages)+3,REG_checks=26,patterns=patterns,code=code,aliases=aliases,details=details,no_RST=True,no_ADL_execution=True,private_code_not_executed=True,first_fault_stage='1',fault_address='0A6000',fault_expected='31',fault_actual='33'),indent=2)+'\n')
print(name,len(b),hashlib.sha256(b).hexdigest())
