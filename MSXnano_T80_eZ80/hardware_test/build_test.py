from pathlib import Path
code=bytearray(); rows=[]; labels={}; fix=[]
def label(n): labels[n]=0x100+len(code); rows.append(n+':')
def emit(bs,comment): code.extend(bs); rows.append('    DEFB '+','.join(f'0{x:02X}H' for x in bs)+' ; '+comment)
def word(bs,target,comment):
 pos=len(code)+len(bs);emit(bs+[0,0],comment);fix.append((pos,target))
label('START')
for pref,val,dst,reg in [([],0x123456,'RESULT','HL'),([0xdd],0x667788,'RESULT_IX','IX'),([0xfd],0x99aabb,'RESULT_IY','IY')]:
 emit([0x5b]+pref+[0x21,val&255,(val>>8)&255,val>>16],f'LD.LIL {reg},{val:06X}h')
 word([0x49]+pref+[0x22],dst,f'LD.LIS ({dst}),{reg} ; 3 data bytes, 2 address bytes')
# reload, then immediately push/pop without print calls
emit([0x5b,0x21,0x56,0x34,0x12,0xe5,0xd1],'LD.LIL HL,123456h / PUSH HL / POP DE')
word([0xed,0x53],'RESULT_PUSH','LD (RESULT_PUSH),DE')
emit([0x21,0xcd,0xab],'LD HL,ABCDh')
word([0x22],'RESULT_SHORT','LD (RESULT_SHORT),HL (2 bytes)')
word([0x21],'RESULT','LD HL,RESULT');word([0x11],'EXPECTED','LD DE,EXPECTED');emit([0x06,14],'LD B,14')
label('COMPARE');emit([0x1a,0xbe],'LD A,(DE) / CP (HL)');word([0xc2],'FAIL','JP NZ,FAIL');emit([0x23,0x13],'INC HL / INC DE');word([0xc3],'NEXT','JP NEXT')
label('NEXT');emit([0x05],'DEC B');word([0xc2],'COMPARE','JP NZ,COMPARE')
word([0x11],'MSG_PASS','LD DE,MSG_PASS');emit([0xaf],'XOR A');word([0xc3],'PRINT','JP PRINT')
label('FAIL');word([0x11],'MSG_FAIL','LD DE,MSG_FAIL');emit([0x3e,1],'LD A,1')
label('PRINT');emit([0x0e,9,0xcd,5,0,0xc9],'LD C,9 / CALL 0005h / RET')
label('RESULT');emit([0]*3,'HL result');label('RESULT_IX');emit([0]*3,'IX result');label('RESULT_IY');emit([0]*3,'IY result');label('RESULT_PUSH');emit([0]*2,'PUSH result');label('RESULT_SHORT');emit([0]*3,'short result plus guard byte')
label('EXPECTED');emit([0x56,0x34,0x12,0x88,0x77,0x66,0xbb,0xaa,0x99,0x56,0x34,0xcd,0xab,0],'expected bytes including guard')
label('MSG_PASS');emit(list(b'EZ80 v4: PASS\r\n$'),'PASS message');label('MSG_FAIL');emit(list(b'EZ80 v4: FAIL\r\n$'),'FAIL message')
for pos,target in fix: code[pos:pos+2]=labels[target].to_bytes(2,'little')
# Byte source is the exact executable encoding, independent of assembler CPU flags.
text='; v4 CPU required. Z80 mode; no ADL mode entry.\n; Generated exact bytes; rebuild using python3 build_test.py.\n    ORG 0100H\n'
# reconstruct resolved DEFB source with instruction comments
idx=0
for row in rows:
 if row.endswith(':'):text+=row+'\n'
 else:
  n=row.split(';')[0].count(',')+1
  text+='    DEFB '+','.join(f'0{x:02X}H' for x in code[idx:idx+n])+' ;'+row.split(';',1)[1]+'\n';idx+=n
root=Path(__file__).parent
(root/'EZ80V4.COM').write_bytes(code);(root/'ez80_test_v4.asm').write_text(text)
print('COM bytes:',len(code))
