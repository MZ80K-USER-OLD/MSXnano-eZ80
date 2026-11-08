from pathlib import Path
import json,random,hashlib
root=Path(__file__).resolve().parent.parent;src=(root/'hardware_test/build_data_r3.py').read_text()
exec(src[:src.index("label('START')")],globals());r=root/'sim/lea_corners';r.mkdir(exist_ok=True)
rows=[];rng=random.Random(0x808)
forms=[('BC','IX',2),('DE','IX',0x12),('HL','IX',0x22),('BC','IY',3),('DE','IY',0x13),('HL','IY',0x23),('IX','IX',0x32),('IY','IX',0x55),('IX','IY',0x54),('IY','IY',0x33)]
def init_af(seed):emit(1,seed,0x81,0xc5,0xf1)
def save_af():emit(0xf5,0xc1);ref([0xed,0x43],'FLAGS')
def check_af(seed):
 la('FLAGS');check(seed,('FLAGS',0));la('FLAGS1');check(0x81,('FLAGS',1))
def lowcheck(labelname,value,count=3):
 for i in range(count):la(labelname+('' if not i else str(i)));check((value>>(8*i))&255,(labelname,i))
def begin():
 n=len(rows);emit(0xf3,0xaf,0x32,0xb2,0,0x32,0xb0,0,0x3e,n,0x32,0xb1,0,0x3e,1,0x32,0xb2,0);return n

def lea(target,source,opcode,pref,base,disp,alternate=0,irq=False):
 n=begin();seed=rng.randrange(256);long=pref in (0x49,0x5b)
 vals={'BC':0xa17788,'DE':0xb26699,'HL':0xc355aa,'IX':0x0b3456,'IY':0x0c789a};vals[source]=base
 # Seed AF before loading BC so the banked BC operand is not disturbed.
 init_af(seed)
 for pair,value in vals.items():loadpair(pair,value)
 loadpair('SP',0x050080)
 if irq:emit(0xfb,0)
 label(f'CASE_{n}_OP');emit(*([] if pref is None else [pref]),0xed,opcode,disp&255);label(f'CASE_{n}_AFTER');emit(0xf3)
 selected=(base+disp)&0xffffff
 expected=selected if long else (vals[target]&0xff0000)|(selected&0xffff)
 vals[target]=expected
 for pair,name in [(target,'RESULT'),('IX','SOURCE'),('IY','OTHER')]:abs_pair(pair,name,pref=0x49)
 save_af();emit(0xaf,0x32,0xb2,0)
 check_af(seed);lowcheck('RESULT',expected);lowcheck('SOURCE',vals['IX']);lowcheck('OTHER',vals['IY']);spcheck(0x050080)
 emit(0x3a,0xb0,0);check(int(irq))
 rows.append(dict(case=n,kind='LEA',target=target,source=source,opcode=opcode,prefix=pref,long=long,base=base,displacement=disp,expected=expected,flags=seed,alternate=alternate,irq=int(irq),write_addresses=[],write_values=[]))

def pea(source,pref,base,disp,stack,irq=False):
 n=begin();seed=rng.randrange(256);long=pref in (0x49,0x5b);size=3 if long else 2;mask=0xffffff if long else 0xffff
 loadpair('IX',0x0b3456);loadpair('IY',0x0c789a);loadpair(source,base);loadpair('SP',stack if long else 0x050080)
 init_af(seed)
 if not long:emit(0x31,stack&255,(stack>>8)&255)
 if irq:emit(0xfb,0)
 opcode=0x65 if source=='IX' else 0x66
 label(f'CASE_{n}_OP');emit(*([] if pref is None else [pref]),0xed,opcode,disp&255);label(f'CASE_{n}_AFTER');emit(0xf3)
 ref([0x49 if long else 0x40,0xed,0x73],'STACK')
 # No PUSH/POP until the actual SPS has been restored.
 if not long:ref([0xed,0x7b],'SAVED_SPS')
 abs_pair(source,'SOURCE',pref=0x49);save_af();emit(0xaf,0x32,0xb2,0)
 check_af(seed);lowcheck('SOURCE',base)
 final=(stack-size)&mask;result=(base+disp)&mask;lowcheck('STACK',final,size)
 if not long:spcheck(0x050080)
 addresses=[(stack-1-i)&mask for i in range(size)];values=[(result>>(8*(size-1-i)))&255 for i in range(size)]
 for addr,value in zip(addresses,values):
  # Unmapped high banks deliberately ignore writes; the bus monitor verifies the attempted transfer.
  if addr<0x1c0000:readcheck(addr,value)
 if 0xffff in addresses:emit(0x3e,0x5c,0x32,0xff,0xff)
 emit(0x3a,0xb0,0);check(int(irq))
 rows.append(dict(case=n,kind='PEA',source=source,opcode=opcode,prefix=pref,long=long,base=base,displacement=disp,stack=stack,final_stack=final,flags=seed,irq=int(irq),write_addresses=addresses,write_values=values))

label('START');emit(0xdd,0xe5,0xfd,0xe5,0xf3);ref([0xed,0x73],'SAVED_SPS');emit(0xed,0x56);gate(0xa5);gate(0x5a)
stage('L')
for target,source,opcode in forms:
 for pref,base,disp in [(None,0x02ffff,1),(0x40,0x030000,-1),(0x49,0xffffff,1),(0x52,0,-128),(0x5b,0x1bff80,127)]:lea(target,source,opcode,pref,base,disp)
stage('A')
main={'BC':0x0b1122,'DE':0x0c3344,'HL':0x0d5566}
for pair,value in main.items():loadpair(pair,value)
emit(0xd9)
for target,source,opcode in forms[:6]:lea(target,source,opcode,0x49,0x02ffff,1,alternate=1)
emit(0xd9)
for pair,value in main.items():abs_pair(pair,'RESULT',pref=0x49);lowcheck('RESULT',value)
stage('P')
for source in ('IX','IY'):
 for pref in (None,0x40,0x49,0x52,0x5b):
  long=pref in (0x49,0x5b);pea(source,pref,0x030000,-128,0x050001 if long else 0xe001)
stage('B')
for source in ('IX','IY'):
 pea(source,0x52,0xffffff,127,1)
 pea(source,0x49,0x02ffff,1,1)
stage('K');gate(0)
emit(0x3e,0x80,0xed,0x54);save_af();la('FLAGS');check(0x87);la('FLAGS1');check(0x80)
for code in (0x55,0x65):ref([0xcd],f'LOCKED_SUB_{code}');check(code)
label('LOCKED_IM');emit(0xed,0x66);label('LOCKED_IM_AFTER');emit(0,0xed,0x56);gate(0xa5);gate(0x5a)
stage('I');lea('IY','IX',0x55,0x49,0x02ffff,1,irq=True);pea('IY',0x49,0x030000,-1,0x050001,irq=True)
ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):la('SPS_SNAPSHOT'+('' if not i else '1'));check(('SAVED_SPS'+('' if not i else '1'),0),('SPS_SNAPSHOT',i))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
for code in (0x55,0x65):label(f'LOCKED_SUB_{code}');emit(0x3e,code,0xed,code)
footer=src[src.index("label('SUBROUTINE')"):].replace('EZ80D3','EZ80L8').replace('`define R3_','`define L8_').replace(' R3',' R8')
extra="label('FLAGS');emit(0,0);labels['FLAGS1']=labels['FLAGS']+1\n"
for name in ('RESULT','SOURCE','OTHER','STACK'):extra+=f"label('{name}');emit(0,0,0);labels['{name}1']=labels['{name}']+1;labels['{name}2']=labels['{name}']+2\n"
footer=footer.replace('for at,name,off,i in bytefix:',extra+'for at,name,off,i in bytefix:')
exec(footer,globals());assert len(b)<0xd000,len(b)
for row in rows:
 n=row['case'];row['opcode_pc']=labels[f'CASE_{n}_OP'];row['after_pc']=labels[f'CASE_{n}_AFTER']
(r/'vectors.json').write_text(json.dumps(rows,indent=2)+'\n')
(r/'EZ80L8.json').write_text(json.dumps(dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),simulation_only=True,fixture_SPS=0xeffa,labels=labels,EA_cases=len(rows),LEA_cases=sum(x['kind']=='LEA' for x in rows),PEA_cases=sum(x['kind']=='PEA' for x in rows)),indent=2)+'\n')
lines=[]
for v in rows:
 n=v['case'];lines.append(f"is_pea[{n}]={int(v['kind']=='PEA')};irq_expected[{n}]={v['irq']};after_pc[{n}]=16'h{v['after_pc']:04x};expected_writes[{n}]={len(v['write_addresses'])};")
 for k,(addr,value) in enumerate(zip(v['write_addresses'],v['write_values'])):lines.append(f"write_addr[{n}*3+{k}]=24'h{addr:06x};write_value[{n}*3+{k}]=8'h{value:02x};")
(r/'case_plan.vh').write_text('\n'.join(lines)+'\n')
print('cases',len(rows),'LEA',sum(x['kind']=='LEA' for x in rows),'writes',sum(len(x['write_addresses']) for x in rows))
