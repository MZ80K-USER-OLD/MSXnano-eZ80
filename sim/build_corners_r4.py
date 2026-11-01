from pathlib import Path
root=Path(__file__).resolve().parent.parent
src=(root/'hardware_test/build_data_r3.py').read_text()
exec(src[:src.index("label('START')")],globals())
r=root/'sim/corners';r.mkdir(exist_ok=True)
def flags_init():emit(1,0xd7,0,0xc5,0xf1)
def flags_save():emit(0xf5,0xc1);ref([0xed,0x43],'FLAGS')
def flags_check():la('FLAGS');emit(0xe6,0xd7);check(0xd7,('FLAGS',0))
def writebyte(address,v):loadpair('HL',address);emit(0x3e,v);indir('HL',True)
label('START');emit(0xdd,0xe5,0xfd,0xe5,0xf3);ref([0xed,0x73],'SAVED_SPS');gate(0xa5);gate(0x5a)
stage('L')
for pref in (0x49,0x5b):
 for pair,index in [('HL',[]),('IX',[0xdd]),('IY',[0xfd])]:
  for base in (0x03ffff,0x1bfffd):
   for i,v in enumerate((0x56,0x34,0x12)):writebyte(base+i,v)
   flags_init();loadpair(pair,0xa7b8c9);loadpair('SP',base);emit(pref,*index,0xe3)
   abs_pair(pair,'SNAP',pref=0x49);flags_save();spcheck(base)
   for i,v in enumerate((0xc9,0xb8,0xa7)):readcheck(base+i,v)
   for i,v in enumerate((0x56,0x34,0x12)):
    la('SNAP'+('' if not i else str(i)));check(v,('SNAP',i))
   flags_check()
stage('S')
for pref in (0x40,0x52):
 for pair,index in [('HL',[]),('IX',[0xdd]),('IY',[0xfd])]:
  flags_init();emit(1,0x34,0x12,0xc5);loadpair(pair,0xa7b8c9);loadpair('SP',0x030100)
  emit(pref,*index,0xe3);abs_pair(pair,'SNAP',pref=0x40);flags_save()
  for i,v in enumerate((0xc9,0xb8)):
   emit(0x3a,0xf8+i,0xef);check(v,0x00eff8+i)
  for i,v in enumerate((0x34,0x12)):
   la('SNAP'+('' if not i else str(i)));check(v,('SNAP',i))
  flags_check();emit(0xc1);spcheck(0x030100)
stage('B')
for pref in (0x40,0x49,0x52):
 flags_init();emit(0x3e,0x5a);ref([pref,0x32],'GUARD')
 if pref==0x52:emit(0x1b)
 ref([pref,0x3a],'GUARD')
 if pref==0x52:emit(0x1b)
 sa('BYTE_RESULT');flags_save();la('BYTE_RESULT');check(0x5a,('GUARD',0));flags_check()
# The fixture's GUARD invariant expects A6 after the tests.
emit(0x3e,0xa6);sa('GUARD')
ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):
 la('SPS_SNAPSHOT'+('' if not i else '1'));check(('SAVED_SPS'+('' if not i else '1'),0),('SPS_SNAPSHOT',i))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
footer=src[src.index("label('SUBROUTINE')"):].replace('EZ80D3','EZ80C4').replace('`define R3_','`define C4_').replace(' R3',' R4')
footer=footer.replace('for at,name,off,i in bytefix:', "label('FLAGS');emit(0,0)\nlabel('SNAP');emit(0,0,0);labels['SNAP1']=labels['SNAP']+1;labels['SNAP2']=labels['SNAP']+2\nlabel('BYTE_RESULT');emit(0)\nfor at,name,off,i in bytefix:")
exec(footer,globals())
