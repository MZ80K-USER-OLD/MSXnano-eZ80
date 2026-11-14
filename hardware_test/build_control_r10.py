"""MSX-DOS safe native ADL flow test; no BIOS vectors, IRQ or mixed frames."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent.parent;src=(root/'hardware_test/build_data_r3.py').read_text()
exec(src[:src.index("label('START')")],globals());r=root/'hardware_test'
base=0x090000;code=[];pl={};pf=[];results=[]
def e(*xs):code.extend(xs)
def lab(n):pl[n]=base+len(code)
def jump(op,n,prefix=()):
 e(*prefix,op);pf.append((len(code),n));e(0,0,0)
def imm(op,v,prefix=()):e(*prefix,op,v&255,(v>>8)&255,v>>16)
def seed(f):imm(0x21,0x00a500|f);e(0xe5,0xf1)
def result(value,desc):
 addr=0x030200+len(results);imm(0x32,addr);results.append(dict(address=addr,value=value,description=desc))
def flags_result(f):
 e(0xf5,0xe1);addr=0x030200+len(results);imm(0x22,addr)
 results.extend([dict(address=addr,value=f,description='flow preserves F'),dict(address=addr+1,value=None,description='AF accumulator snapshot'),dict(address=addr+2,value=0,description='AF upper padding')])
imm(0x31,0x050001)
for cc in range(8):
 mask=[64,64,1,1,4,4,128,128][cc]
 for f in (0,mask):
  yes=bool(f&mask)==bool(cc&1);n=f'{cc}_{f}'
  seed(f);jump(0xc2+8*cc,'J'+n);e(0x3e,0x11);jump(0xc3,'JA'+n);lab('J'+n);e(0x3e,0x22);lab('JA'+n);result(0x22 if yes else 0x11,'JP cc '+n);flags_result(f)
  seed(f);e(0x3e,0x11);jump(0xc4+8*cc,'C'+n);jump(0xc3,'CA'+n);lab('C'+n);e(0x3e,0x22,0xc9);lab('CA'+n);result(0x22 if yes else 0x11,'CALL cc '+n);flags_result(f)
  seed(f);e(0x3e,0x11);jump(0xcd,'R'+n);jump(0xc3,'RA'+n);lab('R'+n);e(0xc0+8*cc,0x3e,0x33,0xc9);lab('RA'+n);result(0x11 if yes else 0x33,'RET cc '+n);flags_result(f)
# All three indirect JP sources in ADL, skipping a wrong-path marker.
for i,pref in enumerate(((),(0xdd,),(0xfd,))):
 n='IND'+str(i);e(0x3e,0x44);e(*pref,0x21);pf.append((len(code),n));e(0,0,0);e(*pref,0xe9,0x3e,0xee);lab(n);result(0x44,'JP indirect '+str(pref))
for op,f,yes in [(0x20,0,1),(0x28,64,1),(0x30,0,1),(0x38,1,1),(0x20,64,0),(0x28,0,0),(0x30,1,0),(0x38,0,0)]:
 seed(f);e(0x3e,0x55,op,2,0x3e,0x66);result(0x55 if yes else 0x66,'JR condition');flags_result(f)
seed(0xc5);e(0x06,3,0x10,0xfe)
e(0x78);result(0,'DJNZ B decremented to zero');flags_result(0xc5)
# Native nested CALL/RET, with private stack crossing 04FFFF/050000.
seed(0xc5);e(0x3e,0x11);jump(0xcd,'OUTER');jump(0xc3,'NEST_DONE');lab('OUTER');jump(0xcd,'INNER');e(0xc9);lab('INNER');e(0x3e,0x77,0xc9);lab('NEST_DONE');result(0x77,'nested CALL RET');flags_result(0xc5)
e(0x40,0xc3,('RETURN',0),('RETURN',1))
for at,n in pf:code[at:at+3]=list(pl[n].to_bytes(3,'little'))
# Header follows the existing R9 /RUN and gate convention.
label('START');emit(0xdd,0xe5,0xfd,0xe5,0xf3);ref([0xed,0x73],'SAVED_SPS')
for addr,val in [(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:emit(0x3a,addr,0,0xfe,val);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
stage('C')
for i,v in enumerate(code):
 loadpair('HL',base+i);emit(0x3e,0)
 if isinstance(v,tuple):bytefix.append((len(b)-1,v[0],0,v[1]))
 else:b[-1]=v
 indir('HL',True)
emit(0x5b,0xc3,base&255,(base>>8)&255,base>>16);label('RETURN')
for row in results:
 if row['value'] is not None:readcheck(row['address'],row['value'])
spcheck(0x050001);ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):la('SPS_SNAPSHOT'+('' if not i else '1'));check(('SAVED_SPS'+('' if not i else '1'),0),('SPS_SNAPSHOT',i))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('MSG_READY');emit(*b'EZ80CTL R10: READY - use /RUN\r\n$')
footer=src[src.index("label('SUBROUTINE')"):].replace('EZ80D3','EZ80CTL').replace('`define R3_','`define CTL_').replace(' R3',' R10')
exec(footer,globals());assert len(b)<0xd000,len(b)
(r/'EZ80CTL.json').write_text(json.dumps(dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),labels=labels,entry=base,payload_bytes=len(code),checks=results,stage=6,requires_R10=True,RST_hardware_tested=False),indent=2)+'\n')
print('EZ80CTL',len(b),'payload',len(code),'checks',sum(x['value'] is not None for x in results))
