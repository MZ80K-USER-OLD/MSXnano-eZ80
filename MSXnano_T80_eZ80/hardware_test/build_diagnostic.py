from pathlib import Path
class Builder:
 def __init__(self):self.data=bytearray();self.records=[];self.labels={};self.fix=[]
 def label(self,n):self.labels[n]=0x100+len(self.data);self.records.append((n,None,''))
 def emit(self,b,c=''):self.records.append((None,len(b),c));self.data.extend(b)
 def word(self,op,n,c=''):p=len(self.data)+len(op);self.emit(op+[0,0],c);self.fix.append((p,n))
 def build(self):
  for p,n in self.fix:self.data[p:p+2]=self.labels[n].to_bytes(2,'little')
  out='; MSX-DOS v4 diagnosis. Byte-encoded exact executable.\n    ORG 0100H\n';p=0
  for n,size,c in self.records:
   if n:out+=n+':\n'
   else:out+='    DEFB '+','.join(f'0{x:02X}H' for x in self.data[p:p+size])+' ; '+c+'\n';p+=size
  return out
b=Builder();b.label('START');b.emit([0xdd,0xe5,0xfd,0xe5],'save caller IX/IY')
for mode in ['DI','EI']:
 b.emit([0xf3] if mode=='DI' else [0xfb,0],'mask / enable interrupts')
 b.word([0xed,0x73],mode+'_SP0','LD (SP0),SP')
 for pref,val,reg in [([],0x123456,'HL'),([0xdd],0x667788,'IX'),([0xfd],0x99aabb,'IY')]:
  b.emit([0x5b]+pref+[0x21,val&255,(val>>8)&255,val>>16],'LD.LIL '+reg)
  b.word([0x49]+pref+[0x22],mode+'_'+reg,'LD.LIS (result),'+reg)
 b.emit([0x5b,0x21,0x56,0x34,0x12,0xe5,0xd1],'long load immediately PUSH HL/POP DE')
 b.word([0xed,0x53],mode+'_PUSH','LD (result),DE')
 b.emit([0x21,0xcd,0xab],'short LD HL,ABCDh')
 b.word([0x22],mode+'_SHORT','short store')
 b.word([0xed,0x73],mode+'_SP1','LD (SP1),SP')
b.emit([0xfb,0],'enable for DOS output')
# render records without any BDOS call until all values are collected
fields=[]
for mode in ['DI','EI']:
 for reg,count in [('HL',3),('IX',3),('IY',3),('PUSH',2),('SHORT',3),('SP0',2),('SP1',2)]:
  for i in range(count):
   b.word([0x3a],mode+'_'+reg+f'_{i}','LD A,(result byte)')
   b.word([0x21],'TEXT_'+mode+'_'+reg+f'_{i}','LD HL,output position')
   b.word([0xcd],'HEX','CALL HEX')
b.word([0x11],'MESSAGE','LD DE,MESSAGE');b.emit([0x0e,9,0xcd,5,0,0xfd,0xe1,0xdd,0xe1,0xc9],'print once, restore IX/IY, return')
b.label('HEX');b.emit([0xf5,0x0f,0x0f,0x0f,0x0f],'PUSH AF / rotate high nibble');b.word([0xcd],'NIBBLE');b.emit([0xf1],'POP AF')
b.label('NIBBLE');b.emit([0xe6,15,0xc6,0x30,0xfe,0x3a],'AND 15 / ADD 30h / CP 3Ah');b.word([0xda],'WRITE','JP C,WRITE');b.emit([0xc6,7],'ADD A,7')
b.label('WRITE');b.emit([0x77,0x23,0xc9],'LD (HL),A / INC HL / RET')
for mode in ['DI','EI']:
 for reg,count in [('HL',3),('IX',3),('IY',3),('PUSH',2),('SHORT',3),('SP0',2),('SP1',2)]:
  b.label(mode+'_'+reg)
  for i in range(count):b.label(mode+'_'+reg+f'_{i}');b.emit([0],'result byte')
b.label('MESSAGE');b.emit(list(b'EZ80 v4 diagnosis (bytes LOW to HIGH)\r\n'),'banner')
expect={'HL':'56 34 12','IX':'88 77 66','IY':'BB AA 99','PUSH':'56 34','SHORT':'CD AB 00','SP0':'same as SP1','SP1':'same as SP0'}
for mode in ['DI','EI']:
 b.emit(list((mode+' block\r\n').encode()))
 for reg,count in [('HL',3),('IX',3),('IY',3),('PUSH',2),('SHORT',3),('SP0',2),('SP1',2)]:
  b.emit(list((reg+' EXPECT='+expect[reg]+' ACTUAL=').encode()))
  for i in range(count):b.label('TEXT_'+mode+'_'+reg+f'_{i}');b.emit(list(b'?? '))
  b.emit([13,10])
b.emit(list(b'DI only passes: suspect IRQ. Upper bytes 00 in both: inspect v4 build/stores.\r\n$'))
r=Path(__file__).parent;(r/'ez80_diagnostic.asm').write_text(b.build());(r/'EZ80DIAG.COM').write_bytes(b.data);print('Diagnostic bytes',len(b.data))
