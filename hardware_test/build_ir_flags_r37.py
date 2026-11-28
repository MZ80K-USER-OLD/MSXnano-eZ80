"""Build a locked-Z80 MSX-DOS test, no BDOS/BIOS calls while I/R are modified."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parent;buf=bytearray();labels={};fix=[]
def emit(*x):buf.extend(x)
def lab(n):assert n not in labels;labels[n]=0x100+len(buf)
def wordlabel(n):fix.append((len(buf),n));emit(0,0)
def jp(n,op=0xc3):emit(op);wordlabel(n)
def call(n):jp(n,0xcd)
def lda(n):emit(0x3a);wordlabel(n)
def sta(n):emit(0x32);wordlabel(n)
def ldde(n):emit(0x11);wordlabel(n)
lab('START');emit(0xf5,0xc5,0xd5,0xe5,0xdd,0xe5,0xfd,0xe5)
emit(0xed,0x57);sta('OLD_I');emit(0x3e,0);jp('IFF_SAVED',0xe2);emit(0x3c)
lab('IFF_SAVED');sta('OLD_IFF');emit(0xf3,0xed,0x5f);sta('OLD_R')
emit(0xaf);sta('WANTED_C');sta('STATUS');sta('VALUE_INDEX');emit(0x06,0)
lab('LOOP')
for kind,op,write in [('I',0x57,0x47),('R',0x5f,0x4f)]:
 emit(0x3e,ord(kind));sta('FAIL_STAGE')
 # Install FE/FF as incoming F, then change A without changing flags.
 lda('WANTED_C');emit(0xf6,0xfe,0x6f,0x26,0,0xe5,0xf1,0x78,0xed,write,0xed,op,0xf5,0xe1)
 if kind=='I':emit(0x50) # expected A = B
 else:emit(0x78,0xc6,2,0xe6,0x7f,0x57,0x78,0xe6,0x80,0xb2,0x57)
 call('EXPECT_FLAGS');call('CHECK_AF')
lda('VALUE_INDEX');emit(0x3c,0xfe,9);jp('NEXT_CARRY',0xca);sta('VALUE_INDEX')
emit(0x5f,0x16,0,0x21);wordlabel('VALUES');emit(0x19,0x46);jp('LOOP')
lab('NEXT_CARRY');lda('WANTED_C');emit(0x3c,0xfe,2);jp('PASS',0xca);sta('WANTED_C');emit(0xaf);sta('VALUE_INDEX');emit(0x06,0);jp('LOOP')
lab('EXPECT_FLAGS');emit(0x7a,0xe6,0x80,0x5f,0x7a,0xb7);jp('EXPECT_NONZERO',0xc2)
emit(0x7b,0xf6,0x40,0x5f)
lab('EXPECT_NONZERO');lda('WANTED_C');emit(0xb3,0x5f,0xc9)
lab('CHECK_AF');emit(0x7c,0xba);jp('FAIL',0xc2);emit(0x7d,0xe6,0xd7,0xbb);jp('FAIL',0xc2);emit(0xc9)
lab('PASS');emit(0x3e,1);sta('STATUS');ldde('PASS_MSG');jp('REPORT')
lab('FAIL');emit(0x78);sta('FAIL_VALUE');emit(0x7a);sta('EXP_A');emit(0x7b);sta('EXP_F');emit(0x7c);sta('ACT_A');emit(0x7d,0xe6,0xd7);sta('ACT_F')
emit(0x3e,2);sta('STATUS')
# CHECK_AF was called; discard its return word before joining report/return.
emit(0xc1)
lda('FAIL_STAGE');sta('PRINT_OP')
lda('WANTED_C');emit(0xc6,ord('0'));sta('PRINT_C')
for src,dst in [('FAIL_VALUE','PRINT_VALUE'),('EXP_A','PRINT_EXP_A'),('EXP_F','PRINT_EXP_F'),('ACT_A','PRINT_ACT_A'),('ACT_F','PRINT_ACT_F')]:
 lda(src);ldde(dst);call('WRITE_HEX')
ldde('FAIL_MSG')
lab('REPORT')
# Restore I and R before any DOS call, while DI remains active.
lda('OLD_I');emit(0xed,0x47);lda('OLD_R');emit(0xed,0x4f)
emit(0xfb,0,0x0e,9,0xcd,5,0,0xf3)
lda('OLD_I');emit(0xed,0x47);lda('OLD_IFF');emit(0xb7);jp('RESTORE_REGS',0xca);emit(0xfb,0)
lab('RESTORE_REGS');emit(0xfd,0xe1,0xdd,0xe1,0xe1,0xd1,0xc1,0xf1,0xc9)
lab('WRITE_HEX');emit(0xf5,0x0f,0x0f,0x0f,0x0f,0xe6,0x0f);call('NIBBLE');emit(0x12,0x13,0xf1,0xe6,0x0f);call('NIBBLE');emit(0x12,0xc9)
lab('NIBBLE');emit(0xfe,10);jp('DIGIT',0xda);emit(0xc6,ord('A')-10,0xc9)
lab('DIGIT');emit(0xc6,ord('0'),0xc9)
for n in ['OLD_I','OLD_R','OLD_IFF','WANTED_C','VALUE_INDEX','STATUS','FAIL_STAGE','FAIL_VALUE','EXP_A','EXP_F','ACT_A','ACT_F']:
 lab(n);emit(0)
lab('GUARD');emit(0xa6)
lab('VALUES');emit(0,1,0x7e,0x7f,0x80,0xfe,0xff,0x55,0xaa)
lab('PASS_MSG');buf.extend(b'EZ80IRF R37: PASS\r\n$')
lab('FAIL_MSG')
parts=[b'EZ80IRF R37: FAIL\r\nOP=',('PRINT_OP',b'?'),b' VAL=',('PRINT_VALUE',b'??'),b' C=',('PRINT_C',b'?'),b' EXP A=',('PRINT_EXP_A',b'??'),b' F=',('PRINT_EXP_F',b'??'),b' ACT A=',('PRINT_ACT_A',b'??'),b' F=',('PRINT_ACT_F',b'??'),b'\r\n$']
for part in parts:
 if isinstance(part,tuple):lab(part[0]);buf.extend(part[1])
 else:buf.extend(part)
for at,n in fix:buf[at:at+2]=labels[n].to_bytes(2,'little')
name='EZ80IRF';(R/(name+'.COM')).write_bytes(buf);(R/(name+'.hex')).write_text('\n'.join(f'{v:02x}' for v in buf)+'\n')
(R/(name+'.vh')).write_text(''.join(f"`define P2_{n} 16'h{a:04x}\n" for n,a in labels.items())+f"`define P2_COM_END 16'h{0xff+len(buf):04x}\n")
meta=dict(name=name,version='R37',labels=labels,bytes=len(buf),sha256=hashlib.sha256(buf).hexdigest(),measured_cases=36,I_values=[0,1,0x7e,0x7f,0x80,0xfe,0xff,0x55,0xaa],R_seed_values=[0,1,0x7e,0x7f,0x80,0xfe,0xff,0x55,0xaa],carry_values=[0,1],IFF2_during_measurement=0,mode='locked Z80',DOS_calls_during_measurement=False,I_restored_before_DOS=True,IFF_restored_after_DOS=True,R_restore='saved value; normal M1 increments resume',F_mask='D7',does_not_change_IM=True)
(R/(name+'.json')).write_text(json.dumps(meta,indent=2)+'\n')
lines=['; R37 resolved executable byte listing: see build_ir_flags_r37.py for construction.','ORG 0100h']+[f'{n} EQU {a:05X}h' for n,a in labels.items()]
for at in range(0,len(buf),16):lines.append('DB '+','.join(f'0{v:02X}h' for v in buf[at:at+16]))
(R/(name+'.asm')).write_text('\n'.join(lines)+'\n');shutil.copy2(R/(name+'.COM'),R.parent/(name+'.COM'))
print(name,len(buf),'bytes',meta['sha256'])
