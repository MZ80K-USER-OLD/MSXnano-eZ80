from pathlib import Path
import random,json
root=Path(__file__).resolve().parent.parent;src=(root/'hardware_test/build_data_r3.py').read_text()
exec(src[:src.index("label('START')")],globals());r=root/'sim/arith_corners';r.mkdir(exist_ok=True)
rows=[];rng=random.Random(0x805)
def flags_init(seed):emit(1,seed,0,0xc5,0xf1)
def flags_save():emit(0xf5,0xc1);ref([0xed,0x43],'FLAGS')
def oracle(op,a,b,c,seed,bits=24):
 mask=(1<<bits)-1;sign=1<<(bits-1);sub=op=='SBC'
 raw=a-b-c if sub else a+b+(c if op=='ADC' else 0);z=raw&mask
 h=(a&0xfff)<((b&0xfff)+c) if sub else (a&0xfff)+(b&0xfff)+(c if op=='ADC' else 0)>0xfff
 cy=raw<0 if sub else raw>mask
 if op=='ADD':f=(seed&0xc4)|(0x10 if h else 0)|int(cy)
 else:
  overflow=((a^b)&(a^z)&sign)!=0 if sub else ((~(a^b))&(a^z)&sign)!=0
  f=(0x80 if z&sign else 0)|(0x40 if z==0 else 0)|(0x10 if h else 0)|(4 if overflow else 0)|(2 if sub else 0)|int(cy)
 return z,f

def one(op,target,source,a,b,carry,seed,pref=0x49):
 bits=24 if pref==0x49 else 16
 if source=='SELF':b=a
 z,f=oracle(op,a,b,carry,seed,bits)
 flags_init(seed);loadpair(target,a)
 if source!='SELF':loadpair(source,b)
 reg={'BC':0,'DE':1,'SELF':2,'SP':3}[source]
 index=[0xdd] if target=='IX' else [0xfd] if target=='IY' else []
 if op=='ADD':emit(pref,*index,0x09+(reg<<4))
 else:emit(pref,0xed,(0x4a if op=='ADC' else 0x42)+(reg<<4))
 abs_pair(target,'RESULT',pref=0x49)
 if source not in ('SELF','SP'):abs_pair(source,'SOURCE',pref=0x49)
 flags_save()
 if source=='SP':spcheck(b)
 for i in range(3 if bits==24 else 2):
  la('RESULT'+('' if not i else str(i)));check((z>>(8*i))&255,('RESULT',i))
 la('FLAGS');emit(0xe6,0xd7);check(f,('FLAGS',0))
 if source not in ('SELF','SP'):
  for i in range(3 if bits==24 else 2):
   la('SOURCE'+('' if not i else str(i)));check((b>>(8*i))&255,('SOURCE',i))
 rows.append(dict(op=op,target=target,source=source,left=a,right=b,carry=carry,seed_flags=seed,bits=bits,result=z,flags=f))
label('START');emit(0xdd,0xe5,0xfd,0xe5,0xf3);ref([0xed,0x73],'SAVED_SPS');gate(0xa5);gate(0x5a)
stage('A')
for target in ('HL','IX','IY'):
 for source in ('BC','DE','SELF','SP'):
  one('ADD',target,source,0xffffff,1,1,0xc5)
  one('ADD',target,source,0x123456,rng.randrange(0x1000000),0,0x12)
stage('C')
for op in ('ADC','SBC'):
 for source in ('BC','DE','SELF','SP'):
  for lhs,rhs,cin in [(0x7fffff,0,1),(0x800000,1,0),(0,0,1),(0x123456,rng.randrange(0x1000000),1)]:
   one(op,'HL',source,lhs,rhs,cin,0xc4|cin)
stage('S')
for pref in (0x40,0x52):
 one('ADD','HL','BC',0xffff,1,1,0xc5,pref)
 one('ADC','HL','DE',0xffff,0,1,0xc5,pref)
 one('SBC','HL','SELF',0,0,1,0xc5,pref)
 # Short ADD reads SPS, not SPL; use the fixture's fixed DOS-style entry stack.
 flags_init(0xc4);loadpair('HL',1);loadpair('SP',0x123456);emit(pref,0x39)
 abs_pair('HL','RESULT',pref=0x40);flags_save();spcheck(0x123456)
 for i,v in enumerate((0xfb,0xef)):
  la('RESULT'+('' if not i else str(i)));check(v,('RESULT',i))
 la('FLAGS');emit(0xe6,0xd7);check(0xc4,('FLAGS',0))
 rows.append(dict(op='ADD',target='HL',source='SPS',bits=16,left=1,right=0xeffa,result=0xeffb,flags=0xc4))
ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):
 la('SPS_SNAPSHOT'+('' if not i else '1'));check(('SAVED_SPS'+('' if not i else '1'),0),('SPS_SNAPSHOT',i))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
footer=src[src.index("label('SUBROUTINE')"):].replace('EZ80D3','EZ80A5').replace('`define R3_','`define A5_').replace(' R3',' R5')
footer=footer.replace('for at,name,off,i in bytefix:',"label('FLAGS');emit(0,0)\nlabel('RESULT');emit(0,0,0);labels['RESULT1']=labels['RESULT']+1;labels['RESULT2']=labels['RESULT']+2\nlabel('SOURCE');emit(0,0,0);labels['SOURCE1']=labels['SOURCE']+1;labels['SOURCE2']=labels['SOURCE']+2\nfor at,name,off,i in bytefix:")
exec(footer,globals())
(r/'vectors.json').write_text(json.dumps(rows,indent=2)+'\n')

(r/'EZ80A5.json').write_text(json.dumps({'bytes':len(b),'sha256':__import__('hashlib').sha256(b).hexdigest(),'labels':labels,'memory':'low memory RESULT/SOURCE/FLAGS and ordinary SPS only','fixture_SPS':0xeffa,'long_cases':56,'short_cases':8},indent=2)+'\n')
