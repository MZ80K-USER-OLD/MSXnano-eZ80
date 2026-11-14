from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent
b=bytearray();labels={};fix=[];lines=[];listing=[]
def label(n):labels[n]=0x100+len(b);lines.append(n+':')
def emit(*v,comment=''):
 listing.append((len(b),len(v),comment))
 b.extend(v);lines.append('    DEFB '+','.join(f'{x:02X}h' for x in v)+(' ; '+comment if comment else ''))
def ref(op,n):
 emit(*op,0,0);fix.append((len(b)-2,n))
def la(n):ref([0x3a],n)
def sa(n):ref([0x32],n)
def check(v):emit(0xfe,v);ref([0xc2],'FAIL')
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
 loadpair('HL',(bank<<16)|0x8000);indir('HL',False);check(0x30+bank)
stage('2')
for n,pair in enumerate(('BC','DE','IX','IY')):
 loadpair(pair,0x020100+n);emit(0x3e,0xa0+n);indir(pair,True);indir(pair,False);check(0xa0+n)
stage('3')
# Indexed carry and borrow, across 64 KiB; compare via another register.
for pair,base,disp,actual,val in [('IX',0x02ffff,1,0x030000,0x96),('IY',0x030000,-1,0x02ffff,0x69)]:
 loadpair(pair,base);emit(0x3e,val);indir(pair,True,disp);loadpair('HL',actual);indir('HL',False);check(val)
# FFFF high address must not write the MSX slot register.
loadpair('HL',0x01ffff);emit(0x3e,0xb6);indir('HL',True);indir('HL',False);check(0xb6)
stage('4')
# LIS uses two immediate bytes, clears upper to 00, and long register data path.
loadpair('HL',0x012345);ref([0x49,0x21],'GUARD');emit(0x3e,0xa6);indir('HL',True,pref=0x49);la('GUARD');check(0xa6)
# SIL consumes THREE immediate bytes, but short data uses bank00.
ref([0x52,0x21],'GUARD');emit(0x1b);emit(0x52,0x7e);check(0xa6)
# SIS consumes two; next INC A is executed, not consumed as an upper byte.
emit(0x3e,0x40);ref([0x40,0x21],'GUARD');emit(0x3c);check(0x41)
# No prefix after LIL must restore short addressing.
loadpair('HL',0x010000);ref([0x21],'GUARD');emit(0x7e);check(0xa6)
stage('5')
loadpair('SP',0x05fedc);ref([0x49,0xed,0x73],'SP_SNAPSHOT')
for i,x in enumerate((0xdc,0xfe,5)):
 # offsets patched below
 ref([0x3a],'SP_SNAPSHOT'+('' if i==0 else str(i)));check(x)
# LIS immediate must zero extend SPL without changing SPS.
loadpair('SP',0x3456,pref=0x49);ref([0x49,0xed,0x73],'SP_SNAPSHOT')
for i,x in enumerate((0x56,0x34,0)):
 ref([0x3a],'SP_SNAPSHOT'+('' if i==0 else str(i)));check(x)
# Ordinary 16-bit SP readback must still match the saved, untouched DOS stack.
ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):
 ref([0x3a],'SPS_SNAPSHOT'+('' if i==0 else '1'))
 ref([0x21],'SAVED_SPS'+('' if i==0 else '1'))
 emit(0xbe);ref([0xc2],'FAIL')
# A Z80 CALL/RET after SPL load proves its bank is not used for control flow.
ref([0xcd],'SUBROUTINE')
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('SUBROUTINE');emit(0xc9)
label('FAIL');emit(0x3e,2);sa('STATUS');ref([0x11],'MSG_FAIL');ref([0xc3],'FINISH')
label('UNSUPPORTED');emit(0x3e,3);sa('STATUS');ref([0x11],'MSG_UNSUPPORTED')
label('FINISH');emit(0xd5);gate(0);emit(0xd1,0xfb,0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9)
label('MSG_PASS');emit(*b'EZ80D1 R1: PASS\r\n$')
label('MSG_UNSUPPORTED');emit(*b'EZ80D1 R1: UNSUPPORTED\r\n$')
label('MSG_FAIL');emit(*b'EZ80D1 R1: FAIL stage ');label('FAIL_STAGE');emit(ord('?'),13,10,36)
label('STATUS');emit(0);label('GUARD');emit(0xa6);label('SP_SNAPSHOT');emit(0,0,0)
labels['SP_SNAPSHOT1']=labels['SP_SNAPSHOT']+1;labels['SP_SNAPSHOT2']=labels['SP_SNAPSHOT']+2
label('SPS_SNAPSHOT');emit(0,0);labels['SPS_SNAPSHOT1']=labels['SPS_SNAPSHOT']+1
label('SAVED_SPS');emit(0,0);labels['SAVED_SPS1']=labels['SAVED_SPS']+1
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
(r/'EZ80D1.COM').write_bytes(b);(r/'EZ80D1.hex').write_text('\n'.join(f'{x:02x}' for x in b)+'\n')
# Fully resolved assembly listing, independently reproducible via byte emitter.
(r/'EZ80D1.asm').write_text('; R1 subset; resolved bytes, no external assembler required\n'+
 '\n'.join(f'{n} EQU 0{v:04X}h' for n,v in labels.items())+'\nORG 0100h\n'+
 '\n'.join('    DEFB '+','.join(f'0{x:02X}h' for x in b[at:at+n])+f' ; {0x100+at:04X} '+comment for at,n,comment in listing)+'\n')
(r/'EZ80D1.json').write_text(json.dumps({'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'labels':labels,'private_addresses':['018000..1B8000 (one byte per bank)','020100..020103','030000','02FFFF','01FFFF'],'not_tested':['ADL code execution','ADL interrupts','VRAM','MegaRAM','24bit stack push/pop']},indent=2)+'\n')
(r/'EZ80D1.vh').write_text(''.join(f'`define R1_{k} 16\'h{v:04x}\n' for k,v in labels.items())+f"`define R1_COM_END 16'h{0xff+len(b):04x}\n")
print('EZ80D1.COM',len(b),'bytes',hashlib.sha256(b).hexdigest())
