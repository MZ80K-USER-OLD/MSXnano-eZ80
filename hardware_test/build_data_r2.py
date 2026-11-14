from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent
b=bytearray();labels={};fix=[];lines=[];listing=[];bytefix=[]
def label(n):labels[n]=0x100+len(b);lines.append(n+':')
def emit(*v,comment=''):
 listing.append((len(b),len(v),comment))
 b.extend(v);lines.append('    DEFB '+','.join(f'{x:02X}h' for x in v)+(' ; '+comment if comment else ''))
def ref(op,n):
 emit(*op,0,0);fix.append((len(b)-2,n))
def la(n):ref([0x3a],n)
def sa(n):ref([0x32],n)
def address_context(address):
 if address is None:
  emit(0x3e,0);sa('DIAG_MEM')
 else:
  emit(0x3e,1);sa('DIAG_MEM')
  for i in range(3):
   emit(0x3e,0)
   if isinstance(address,tuple):bytefix.append((len(b)-1,address[0],address[1],i))
   else:b[-1]=(address>>(8*i))&255
   sa('DIAG_ADDR'+str(i))
def check(v,address=None):
 sa('DIAG_ACT')
 if isinstance(v,tuple):
  ref([0x21],v[0]);emit(0xbe)
 else:emit(0xfe,v)
 next_label='CHECK_OK_'+str(len(b));ref([0xca],next_label)
 if isinstance(v,tuple):la(v[0])
 else:emit(0x3e,v)
 sa('DIAG_EXP');address_context(address);ref([0xc3],'FAIL');label(next_label)
def readcheck(address,value):
 loadpair('HL',address);indir('HL',False);check(value,address)
def spcheck(expected):
 ref([0x49,0xed,0x73],'SP_SNAPSHOT')
 for i in range(3):
  la('SP_SNAPSHOT'+('' if i==0 else str(i)));check((expected>>(8*i))&255,('SP_SNAPSHOT',i))
def stackop(pair,push,pref=0x5b):
 op={'BC':[0xc5 if push else 0xc1],'DE':[0xd5 if push else 0xd1],'HL':[0xe5 if push else 0xe1], 'IX':[0xdd,0xe5 if push else 0xe1],'IY':[0xfd,0xe5 if push else 0xe1],'AF':[0xf5 if push else 0xf1]}[pair]
 emit(pref,*op)
def incdec(pair,decrement):
 op={'BC':[0x0b if decrement else 3],'DE':[0x1b if decrement else 0x13],'HL':[0x2b if decrement else 0x23],'IX':[0xdd,0x2b if decrement else 0x23],'IY':[0xfd,0x2b if decrement else 0x23],'SP':[0x3b if decrement else 0x33]}[pair]
 emit(0x5b,*op)
def snapshot_pair(pair,value):
 loadpair('SP',0x060103);stackop(pair,True)
 for i in range(3):readcheck(0x060100+i,(value>>(8*i))&255)

def stage(c):emit(0x3e,ord(c));sa('FAIL_STAGE')
def loadpair(pair,value,pref=0x5b):
 op={'BC':[1],'DE':[0x11],'HL':[0x21],'IX':[0xdd,0x21],'IY':[0xfd,0x21],'SP':[0x31]}[pair]
 emit(pref,*op,value&255,(value>>8)&255,*([(value>>16)&255] if pref&0x10 else []),comment=f'LD suffix={pref:02X} {pair},{value:06X}h')
def gate(v):emit(1,0xe7,0xe7,0x3e,v,0xed,0x79)
def indir(pair,write,disp=0,pref=0x5b):
 op={'BC':[2 if write else 0xa],'DE':[0x12 if write else 0x1a],'HL':[0x77 if write else 0x7e], 'IX':[0xdd,0x77 if write else 0x7e,disp&255],'IY':[0xfd,0x77 if write else 0x7e,disp&255]}[pair]
 emit(pref,*op)
label('START');emit(0xdd,0xe5,0xfd,0xe5,0xf3,comment='Save DOS IX/IY; DI. SPS and PC stay Z80 throughout.')
ref([0xed,0x73],'SAVED_SPS')
gate(0xa5);gate(0x5a);emit(0xed,0x78);check_status=len(b);emit(0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
stage('1')
# Unique patterns for all 27 private banks, then read in reverse to detect aliases.
for bank in range(1,28):
 loadpair('HL',(bank<<16)|0x8000);emit(0x3e,0x30+bank);indir('HL',True)
for bank in range(27,0,-1):
 loadpair('HL',(bank<<16)|0x8000);indir('HL',False);check(0x30+bank,(bank<<16)|0x8000)
stage('2')
for n,pair in enumerate(('BC','DE','IX','IY')):
 loadpair(pair,0x020100+n);emit(0x3e,0xa0+n);indir(pair,True);indir(pair,False);check(0xa0+n,0x020100+n)
stage('3')
# Indexed carry and borrow, across 64 KiB; compare via another register.
for pair,base,disp,actual,val in [('IX',0x02ffff,1,0x030000,0x96),('IY',0x030000,-1,0x02ffff,0x69)]:
 loadpair(pair,base);emit(0x3e,val);indir(pair,True,disp);loadpair('HL',actual);indir('HL',False);check(val,actual)
# FFFF high address must not write the MSX slot register.
loadpair('HL',0x01ffff);emit(0x3e,0xb6);indir('HL',True);indir('HL',False);check(0xb6,0x01ffff)
stage('4')
# LIS uses two immediate bytes, clears upper to 00, and long register data path.
loadpair('HL',0x012345);ref([0x49,0x21],'GUARD');emit(0x3e,0xa6);indir('HL',True,pref=0x49);la('GUARD');check(0xa6,('GUARD',0))
# SIL consumes THREE immediate bytes, but short data uses bank00.
ref([0x52,0x21],'GUARD');emit(0x1b);emit(0x52,0x7e);check(0xa6,('GUARD',0))
# SIS consumes two; next INC A is executed, not consumed as an upper byte.
emit(0x3e,0x40);ref([0x40,0x21],'GUARD');emit(0x3c);check(0x41)
# No prefix after LIL must restore short addressing.
loadpair('HL',0x010000);ref([0x21],'GUARD');emit(0x7e);check(0xa6,('GUARD',0))
stage('5')
loadpair('SP',0x05fedc);ref([0x49,0xed,0x73],'SP_SNAPSHOT')
for i,x in enumerate((0xdc,0xfe,5)):
 # offsets patched below
 ref([0x3a],'SP_SNAPSHOT'+('' if i==0 else str(i)));check(x,('SP_SNAPSHOT',i))
# LIS immediate must zero extend SPL without changing SPS.
loadpair('SP',0x3456,pref=0x49);ref([0x49,0xed,0x73],'SP_SNAPSHOT')
for i,x in enumerate((0x56,0x34,0)):
 ref([0x3a],'SP_SNAPSHOT'+('' if i==0 else str(i)));check(x,('SP_SNAPSHOT',i))
# Ordinary 16-bit SP readback must still match the saved, untouched DOS stack.
ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):
 la('SPS_SNAPSHOT'+('' if i==0 else '1'));check(('SAVED_SPS'+('' if i==0 else '1'),0),('SPS_SNAPSHOT',i))
stage('6')
for pair in ('BC','DE','HL','IX','IY','SP'):
 for initial,dec,expected in [(0x00ffff,False,0x010000),(0x010000,True,0x00ffff),(0xffffff,False,0),(0,True,0xffffff),(0x123456,False,0x123457)]:
  loadpair(pair,initial);incdec(pair,dec)
  if pair=='SP':spcheck(expected)
  else:snapshot_pair(pair,expected)
stage('7')
for pair in ('BC','DE','HL','IX','IY'):
 for pref in (0x5b,0x49):
  loadpair('SP',0x050001);loadpair(pair,0x123456);stackop(pair,True,pref)
  spcheck(0x04fffe)
  # HL checks may overwrite the source register, but POP must reconstruct it.
  for i,x in enumerate((0x56,0x34,0x12)):readcheck(0x04fffe+i,x)
  stackop(pair,False,pref)
  spcheck(0x050001);snapshot_pair(pair,0x123456)
# Three-byte AF frame is [F,A,00]. Preserve exact original flags as expected.
loadpair('SP',0x050001);emit(0x3e,0x81,0x37,0xf5,0xc1);ref([0xed,0x43],'SAVED_AF')
stackop('AF',True);emit(0xaf);stackop('AF',False)
stackop('AF',True)
readcheck(0x04fffe,('SAVED_AF',0));readcheck(0x04ffff,0x81);readcheck(0x050000,0)
spcheck(0x04fffe)
stage('8')
# Explicit short stack operations while extensions are enabled use SPS.
loadpair('SP',0x060100)
for pref in (0x40,0x52):
 emit(1,0x78,0x56);stackop('BC',True,pref);emit(1,0,0);stackop('BC',False,pref)
 ref([0xed,0x43],'PAIR_SNAPSHOT')
 for i,x in enumerate((0x78,0x56)):
  la('PAIR_SNAPSHOT'+('' if i==0 else '1'));check(x,('PAIR_SNAPSHOT',i))
 spcheck(0x060100)
ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):
 la('SPS_SNAPSHOT'+('' if i==0 else '1'));check(('SAVED_SPS'+('' if i==0 else '1'),0),('SPS_SNAPSHOT',i))
# A Z80 CALL/RET after SPL load proves its bank is not used for control flow.
ref([0xcd],'SUBROUTINE')
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('SUBROUTINE');emit(0xc9)
label('FAIL');emit(0x3e,2);sa('STATUS');ref([0x11],'MSG_FAIL');ref([0xc3],'FINISH')
label('UNSUPPORTED');emit(0x3e,3);sa('STATUS');ref([0x11],'MSG_UNSUPPORTED')
label('FINISH');emit(0xd5);gate(0);emit(0xd1);la('STATUS');emit(0xfe,2);ref([0xcc],'FORMAT_DIAG');emit(0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)
# These are exclusively ordinary Z80 helpers, running with extensions locked.
label('FORMAT_DIAG');ref([0x21],'HEX_ADDR');la('DIAG_MEM');emit(0xb7);ref([0xca],'FORMAT_REG')
for i in (2,1,0):la('DIAG_ADDR'+str(i));ref([0xcd],'HEX_BYTE')
ref([0xc3],'FORMAT_VALUES')
label('FORMAT_REG')
for i in range(6):emit(0x36,ord('-'),0x23)
label('FORMAT_VALUES');ref([0x21],'HEX_EXP');la('DIAG_EXP');ref([0xcd],'HEX_BYTE')
ref([0x21],'HEX_ACT');la('DIAG_ACT');ref([0xcd],'HEX_BYTE');emit(0xc9)
label('HEX_BYTE');emit(0xf5,0x0f,0x0f,0x0f,0x0f);ref([0xcd],'HEX_NIBBLE');emit(0xf1);ref([0xcd],'HEX_NIBBLE');emit(0xc9)
label('HEX_NIBBLE');emit(0xe6,0x0f,0xc6,0x30,0xfe,0x3a);ref([0xda],'HEX_STORE');emit(0xc6,7)
label('HEX_STORE');emit(0x77,0x23,0xc9)
label('MSG_PASS');emit(*b'EZ80D2 R2: PASS\r\n$')
label('MSG_UNSUPPORTED');emit(*b'EZ80D2 R2: UNSUPPORTED\r\n$')
label('MSG_FAIL');emit(*b'EZ80D2 R2: FAIL stage ');label('FAIL_STAGE');emit(ord('?'),13,10,*b'ADDR=');label('HEX_ADDR');emit(*b'000000 EXP=');label('HEX_EXP');emit(*b'00 ACT=');label('HEX_ACT');emit(*b'00\r\n$')
label('STATUS');emit(0);label('GUARD');emit(0xa6);label('SP_SNAPSHOT');emit(0,0,0)
labels['SP_SNAPSHOT1']=labels['SP_SNAPSHOT']+1;labels['SP_SNAPSHOT2']=labels['SP_SNAPSHOT']+2
label('SPS_SNAPSHOT');emit(0,0);labels['SPS_SNAPSHOT1']=labels['SPS_SNAPSHOT']+1
label('SAVED_SPS');emit(0,0);labels['SAVED_SPS1']=labels['SAVED_SPS']+1
label('DIAG_MEM');emit(0)
for i in range(3):label('DIAG_ADDR'+str(i));emit(0)
label('DIAG_EXP');emit(0);label('DIAG_ACT');emit(0)
label('SAVED_AF');emit(0,0)
label('PAIR_SNAPSHOT');emit(0,0);labels['PAIR_SNAPSHOT1']=labels['PAIR_SNAPSHOT']+1
for at,name,off,i in bytefix:b[at]=((labels[name]+off)>>(8*i))&255
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
(r/'EZ80D2.COM').write_bytes(b);(r/'EZ80D2.hex').write_text('\n'.join(f'{x:02x}' for x in b)+'\n')
# Fully resolved assembly listing, independently reproducible via byte emitter.
(r/'EZ80D2.asm').write_text('; R2 subset; resolved bytes, no external assembler required\n'+
 '\n'.join(f'{n} EQU 0{v:04X}h' for n,v in labels.items())+'\nORG 0100h\n'+
 '\n'.join('    DEFB '+','.join(f'0{x:02X}h' for x in b[at:at+n])+f' ; {0x100+at:04X} '+comment for at,n,comment in listing)+'\n')
(r/'EZ80D2.json').write_text(json.dumps({'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'labels':labels,'private_addresses':['018000..1B8000 (one byte per bank)','020100..020103','030000','02FFFF','01FFFF','060100..060102','04FFFE..050000'],'diagnostics':'first mismatch: ADDR=24bit logical, EXP=8bit, ACT=8bit; register-only ADDR=------','not_tested':['ADL code execution','ADL interrupts','VRAM','MegaRAM','ADL stack frames for control flow']},indent=2)+'\n')
(r/'EZ80D2.vh').write_text(''.join(f'`define R2_{k} 16\'h{v:04x}\n' for k,v in labels.items())+f"`define R2_COM_END 16'h{0xff+len(b):04x}\n")
print('EZ80D2.COM',len(b),'bytes',hashlib.sha256(b).hexdigest())
