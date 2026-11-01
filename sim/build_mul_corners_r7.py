from pathlib import Path
import json,random,hashlib
root=Path(__file__).resolve().parent.parent;src=(root/'hardware_test/build_data_r3.py').read_text()
exec(src[:src.index("label('START')")],globals());r=root/'sim/mul_corners';r.mkdir(exist_ok=True)
rows=[];rng=random.Random(0x807)
def init_af(seed,acc=0x81):emit(1,seed,acc,0xc5,0xf1)
def save_af():emit(0xf5,0xfd,0xe1);ref([0xfd,0x22],'FLAGS')
def check_af(seed,acc=0x81):
 la('FLAGS');check(seed,('FLAGS',0));la('FLAGS1');check(acc,('FLAGS',1))
def check_pair(pair,value):
 abs_pair(pair,'RESULT',pref=0x49)
 for i in range(3):la('RESULT'+('' if i==0 else str(i)));check((value>>(8*i))&255,('RESULT',i))
def op(pair,pref):emit(*([] if pref is None else [pref]),0xed,{'BC':0x4c,'DE':0x5c,'HL':0x6c,'SP':0x7c}[pair])
label('START');emit(0xdd,0xe5,0xfd,0xe5,0xf3);ref([0xed,0x73],'SAVED_SPS');emit(0xed,0x56);gate(0xa5);gate(0x5a)
stage('R')
for bank in (0,1):
 if bank:emit(0xd9)
 for pair in ('BC','DE','HL'):
  for pref in (None,0x40,0x49,0x52,0x5b):
   # Two independent patterns per register/width/bank, with boundary operands.
   for value in (0xffff,rng.choice([0x00ff,0x0101,0x807f,0x55aa,0x1020])):
    seed=rng.randrange(256);init_af(seed)
    values={'BC':0x0b1357,'DE':0x0c2468,'HL':0x0d369a};values[pair]=0xa10000|value
    for name,v in values.items():loadpair(name,v)
    op(pair,pref);save_af();check_af(seed)
    values[pair]=0xa10000|((value>>8)*(value&255))
    for name,v in values.items():check_pair(name,v)
    rows.append(dict(pair=pair,prefix=pref,alternate=bank,input=value,expected=values[pair],flags=seed))
 if bank:emit(0xd9)
stage('S')
for pref in (None,0x40,0x49,0x52,0x5b):
 for value in (0x0102,0xffff):
  long=pref in (0x49,0x5b);seed=rng.randrange(256);init_af(seed)
  loadpair('SP',(0x0b0000|value) if long else 0x0b1357)
  if not long:emit(0x31,value&255,value>>8)
  op('SP',pref)
  # Capture without using either stack, then restore SPS before saving AF.
  ref([0x49 if long else 0x40,0xed,0x73],'RESULT')
  ref([0xed,0x7b],'SAVED_SPS');save_af();check_af(seed)
  expected=(value>>8)*(value&255)
  for i in range(3 if long else 2):
   la('RESULT'+('' if not i else str(i)));check(((0x0b0000|expected)>>(8*i))&255,('RESULT',i))
  spcheck((0x0b0000|expected) if long else 0x0b1357)
  rows.append(dict(pair='SP',prefix=pref,input=value,expected=expected,upper_preserved=True,selected_stack='SPL' if long else 'SPS',flags=seed))
stage('L')
# Preserve the original Z80 undocumented NEG aliases while locked.
gate(0)
for code in (0x4c,0x5c,0x6c,0x7c):
 emit(1,0x22,0x11,0x3e,0x80,0xed,code);save_af();check_af(0x87,0x80)
 ref([0xed,0x43],'RESULT')
 la('RESULT');check(0x22);la('RESULT1');check(0x11)
gate(0xa5);gate(0x5a)
stage('I');loadpair('HL',0xa1ffff);loadpair('SP',0x0b1357);init_af(0xa5)
emit(0xaf,0x32,0xb0,0,0x3e,1,0x32,0xb2,0);init_af(0xa5)
emit(0xfb,0);label('IRQ_MLT');op('HL',0x49);label('IRQ_AFTER');emit(0xf3);save_af();emit(0xaf,0x32,0xb2,0)
check_af(0xa5);check_pair('HL',0xa1fe01);spcheck(0x0b1357);emit(0x3a,0xb0,0);check(1)
rows.append(dict(pair='HL',prefix=0x49,input=0xffff,expected=0xa1fe01,IRQ=True,flags=0xa5))
ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):la('SPS_SNAPSHOT'+('' if not i else '1'));check(('SAVED_SPS'+('' if not i else '1'),0),('SPS_SNAPSHOT',i))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
footer=src[src.index("label('SUBROUTINE')"):].replace('EZ80D3','EZ80M7').replace('`define R3_','`define M7_').replace(' R3',' R7')
footer=footer.replace('for at,name,off,i in bytefix:',"label('FLAGS');emit(0,0);labels['FLAGS1']=labels['FLAGS']+1\nlabel('RESULT');emit(0,0,0);labels['RESULT1']=labels['RESULT']+1;labels['RESULT2']=labels['RESULT']+2\nfor at,name,off,i in bytefix:")
exec(footer,globals())
assert len(b)<0xd000,len(b)
(r/'vectors.json').write_text(json.dumps(rows,indent=2)+'\n')
(r/'EZ80M7.json').write_text(json.dumps({'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'labels':labels,'simulation_only':True,'MLT_cases':len(rows),'locked_NEG_alias_cases':4,'fixture_SPS':0xeffa},indent=2)+'\n')
