"""Independent small architectural oracle for stage6 bus-level tests."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent;d=r/'flow_r10';d.mkdir(exist_ok=True)
mem={};labels={};fix=[];p=0x01e000

def emit(*bs):
 global p
 for x in bs:mem[p]=x;p=(p+1)&0xffffff

def label(n):labels[n]=p

def target(op,n,prefix=()):
 emit(*prefix,op);fix.append((p,n));emit(0,0,0)

def imm(op,v,prefix=()):emit(*prefix,op,v&255,(v>>8)&255,v>>16)
def flags(v):imm(0x21,0x00a500|v);emit(0xe5,0xf1)
def skiptrap():emit(0x76)
imm(0x31,0x050001)
# Every condition bit in each polarity: conditional JP/CALL/RET.
for cc in range(8):
 mask=[0x40,0x40,1,1,4,4,0x80,0x80][cc]
 for f in (0,mask):
  n=f'{cc}_{f}';flags(f)
  target(0xc2+cc*8,'J'+n);emit(0);label('J'+n)
  target(0xc4+cc*8,'C'+n);target(0xc3,'A'+n)
  label('C'+n);emit(0,0xc9);label('A'+n)
  target(0xcd,'R'+n);target(0xc3,'E'+n)
  label('R'+n);emit(0xc0+cc*8,0,0xc9);label('E'+n)
# Nested frames, return PC crosses a 64K boundary.
target(0xc3,'BOUND')
p=0x02fffe;label('BOUND');target(0xcd,'NEST');target(0xc3,'CONT')
p=0x040100;label('NEST');target(0xcd,'INNER');emit(0xc9);label('INNER');emit(0,0xc9)
p=0x030100;label('CONT')
for prefix,name in [((),'HL'),((0xdd,),'IX'),((0xfd,),'IY')]:
 imm(0x21,p+len(prefix)*2+6,prefix);emit(*prefix,0xe9);skiptrap();emit(0)
# JR/DJNZ: forward/back, signed +/-128 and boundary crossings.
for cc,f in [(0x20,0),(0x28,0x40),(0x30,0),(0x38,1),(0x20,0x40),(0x28,0),(0x30,1),(0x38,0)]:
 flags(f);emit(cc,1,0,0)
emit(0x06,3);label('LOOP');emit(0,0x10,0xfd)
# Zero B underflows and loops 256 times, flags preserved.
emit(0x06,0,0x10,0xfe)
# 64K relative forward/back edges, JR plus/minus 128.
target(0xc3,'JRF');p=0x05fffe;label('JRF');emit(0x18,0x7f)
p=0x06007f;emit(0x18,0x80)
p=0x060001;emit(0x18,2)
p=0x060005;target(0xc3,'RST')
p=0x070000;label('RST');flags(0xc5)
for v in range(8):emit(0xc7+v*8)
# Conditional mode transitions: false JP consumes its full operand without changing ADL.
flags(0)
emit(0x40,0xca,0,0x10,0x40,0xc2,0,0x10)
label('AFTER_MODE_JP')
saved=p;p=0x001000;target(0xca,'AFTER_MODE_JP',(0x5b,));target(0xc2,'AFTER_MODE_JP',(0x5b,));p=saved
# JR full24 wrap to bank00, independent of the stack-wrap test.
jump_saved=p
target(0xc3,'JR24');label('AFTER_JR24')
saved=p;p=0xfffffe;label('JR24');emit(0x18,0x7f)
p=0x00007f;target(0xc3,'AFTER_JR24');p=saved
# SP full24 wrap. Stack accesses include 000000, FFFFFF and FFFFFE.
imm(0x31,1);target(0xcd,'WRAP');target(0xc3,'EXIT')
p=0x080010;label('WRAP');emit(0xc9)
p=0x080100;label('EXIT');emit(0x40,0xc3,0,2)
for at,n in fix:
 v=labels[n]
 for i in range(3):mem[at+i]=(v>>(8*i))&255
# Actual reset bootloader: DI, SPS, gate, JP.LIL.
boot=[0xc3,0,1];mem.update(enumerate(boot))
boot=[0xf3,0x31,0,0xf0,0x01,0xe7,0xe7,0x3e,0xa5,0xed,0x79,0x3e,0x5a,0xed,0x79,0x5b,0xc3,0,0xe0,1]
mem.update({0x100+i:v for i,v in enumerate(boot)})
# Oracle starts after boot, with vector slots supplied by the RAM fixture.
state=dict(pc=0x01e000,sp=0xffffff,f=0,a=0x5a,b=0xe7,adl=1,hl=0,ix=0,iy=0);trace=[];writes=[];reads=[];counts={}
m=dict(mem)
for v in range(8):m[v*8]=0xc9
mask24=0xffffff

def get():
 pc=state['pc'];state['pc']=(pc+1)&(mask24 if state['adl'] else 0xffff);return m.get(pc,0)
def u24():return get()|(get()<<8)|(get()<<16)
def cond(cc):
 f=state['f'];return [not(f&64),bool(f&64),not(f&1),bool(f&1),not(f&4),bool(f&4),not(f&128),bool(f&128)][cc]
def push(v):
 for shift in (16,8,0):
  state['sp']=(state['sp']-1)&mask24;a=state['sp'];x=(v>>shift)&255;m[a]=x;writes.append((a,x))
def pop():
 v=0
 for shift in (0,8,16):
  a=state['sp'];x=m.get(a,0);reads.append((a,x));v|=x<<shift;state['sp']=(a+1)&mask24
 return v
for step in range(10000):
 pc=state['pc'];op=get();trace.append(dict(pc=pc,op=op,sp=state['sp'],f=state['f'],adl=state['adl']));counts[f'{op:02X}']=counts.get(f'{op:02X}',0)+1
 if op==0:continue
 if op==0x31:state['sp']=u24()
 elif op==0x21:state['hl']=u24()
 elif op in (0xdd,0xfd):
  sub=get();trace.append(dict(pc=(pc+1)&mask24,op=sub,sp=state['sp'],f=state['f'],adl=state['adl']));key='ix' if op==0xdd else 'iy'
  if sub==0x21:state[key]=u24()
  elif sub==0xe9:state['pc']=state[key]
  else:raise ValueError(sub)
 elif op==0xe5:push(state['hl'])
 elif op==0xf1:v=pop();state['f']=v&255;state['a']=(v>>8)&255
 elif op==0x06:state['b']=get()
 elif op==0xe9:state['pc']=state['hl']
 elif op==0xcd or op&0xc7==0xc4:
  dst=u24()
  if op==0xcd or cond((op>>3)&7):push(state['pc']);state['pc']=dst
 elif op==0xc9 or op&0xc7==0xc0:
  if op==0xc9 or cond((op>>3)&7):state['pc']=pop()
 elif op&0xc7==0xc7:push(state['pc']);state['pc']=op&0x38
 elif op==0xc3 or op&0xc7==0xc2:
  dst=u24()
  if op==0xc3 or cond((op>>3)&7):state['pc']=dst
 elif op in (0x18,0x20,0x28,0x30,0x38,0x10):
  disp=get();disp=disp-256 if disp&128 else disp
  if op==0x10:state['b']=(state['b']-1)&255;take=state['b']!=0
  else:take=op==0x18 or cond((op-0x20)//8)
  if take:state['pc']=(state['pc']+disp)&mask24
 elif op in (0x40,0x5b):
  nextpc=state['pc'];sub=get();trace.append(dict(pc=nextpc,op=sub,sp=state['sp'],f=state['f'],adl=state['adl']))
  assert sub==0xc3 or sub&0xc7==0xc2
  dst=u24() if op==0x5b else get()|(get()<<8)
  if sub==0xc3 or cond((sub>>3)&7):state['pc']=dst;state['adl']=int(op==0x5b)
  if state['pc']==0x200:break
 else:raise ValueError(f'{pc:06X} {op:02X}')
else:raise RuntimeError('oracle loop')
lines=['// Generated sparse image and independent architectural expectations.']
for a,v in sorted(mem.items()):lines.append(f"mem[24'h{a:06x}]=8'h{v:02x};")
for i,t in enumerate(trace):lines.append(f"epc[{i}]=24'h{t['pc']:06x};eop[{i}]=8'h{t['op']:02x};esp[{i}]=24'h{t['sp']:06x};ef[{i}]=8'h{t['f']:02x};eadl[{i}]={t['adl']};")
for typ,rows in [('w',writes),('r',reads)]:
 for i,(a,v) in enumerate(rows):lines.append(f"e{typ}a[{i}]=24'h{a:06x};e{typ}d[{i}]=8'h{v:02x};")
lines.append(f'nfetch={len(trace)};nwrites={len(writes)};nreads={len(reads)};')
(d/'plan.vh').write_text('\n'.join(lines)+'\n');(d/'oracle.json').write_text(json.dumps(dict(trace=trace,writes=writes,reads=reads,op_counts=counts,simulation_only=True),indent=2)+'\n')
print('flow oracle',len(trace),'fetches',len(writes),'stack writes',len(reads),'stack reads')
