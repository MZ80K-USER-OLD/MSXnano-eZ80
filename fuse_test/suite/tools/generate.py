"""Deterministic full opcode-space generator; expectations come from pinned CEmu."""
from pathlib import Path
import ctypes as C, json, csv, hashlib, re, sys
ROOT=Path(__file__).resolve().parents[1]
U=C.c_uint; A=U*22; B=C.c_ubyte*16
FIELDS='AF BC DE HL AF2 BC2 DE2 HL2 IX IY SPL PC I R IFF1 IFF2 IM HALTED ADL MBASE MADL SPS'.split()
oracle=C.CDLL(str(ROOT/'tools/oracle.so')); dis=C.CDLL(str(ROOT/'tools/dis.so'))
dis.disassemble.restype=C.c_char_p
SUFFIX=[None,0x40,0x49,0x52,0x5b]
ED_BLOCK={0x82,0x83,0x84,0x8a,0x8b,0x8c,0x92,0x93,0x94,0x9a,0x9b,0x9c,*range(0xa0,0xa5),*range(0xa8,0xad),*range(0xb0,0xb5),*range(0xb8,0xbd),0xc2,0xc3,0xca,0xcb}
IO_BLOCK=ED_BLOCK-{0xa0,0xa1,0xa8,0xa9,0xb0,0xb1,0xb8,0xb9}
def decode(code,adl=1):
 b=B(*(code+[0]*(16-len(code))))
 return dis.disassemble(b,adl).decode(),dis.instruction_size(b,adl)
def catalog():
 out=[]
 for space in ['BASE','CB','ED','DD','FD','DDCB','FDCB']:
  for op in range(256):
   if space=='BASE' and op in [0x40,0x49,0x52,0x5b,0xcb,0xdd,0xed,0xfd]:continue
   if space in ('DD','FD') and op in [0xcb,0xdd,0xed,0xfd]:continue
   if space=='ED' and op in (0x30,0x70):continue # undocumented flag-only IN encodings; blank in UM0077 Table 109
   head={'BASE':[], 'CB':[0xcb], 'ED':[0xed], 'DD':[0xdd], 'FD':[0xfd], 'DDCB':[0xdd,0xcb,0], 'FDCB':[0xfd,0xcb,0]}[space]+[op]
   name,size=decode(head)
   if not name or name.startswith(('TRAP','NONI')):continue
   # Unassigned CB SLL opcodes are TRAP in zdis; indexed CB only z=6 is documented.
   out.append(dict(key=f'{space}_{op:02X}',space=space,opcode=op,head=head,mnemonic=name.split()[0],assembly=name,length_adl1=size))
 return out
def execute(initial,memory,steps=1,events=None,io_seed=0x5a):
 oracle.reset_case(io_seed)
 for a,v in memory.items():oracle.poke(int(a,16),v)
 oracle.set_state(A(*(initial[k] for k in FIELDS)))
 for i in range(steps):
  if oracle.run_step((events or {}).get(i,0)):raise RuntimeError('oracle opcode trap')
 a=A();oracle.get_state(a);state=dict(zip(FIELDS,a))
 # UM0077 LD A,I / LD A,R specifies PV=IEF2. Pinned CEmu uses IEF1.
 # Correct only this independently specified output bit, outside the emulator.
 if steps==1 and not events:
  pc=initial['PC'] if initial['ADL'] else (initial['MBASE']<<16)|(initial['PC']&65535)
  bs=[memory.get(f'{((pc+i)&0xffffff) if initial["ADL"] else ((initial["MBASE"]<<16)|((pc+i)&65535)):06x}',0) for i in range(8)]
  while bs and bs[0] in (0x40,0x49,0x52,0x5b):bs.pop(0)
  if len(bs)>1 and bs[0]==0xed and bs[1] in (0x57,0x5f):
   state['AF']=(state['AF']&~4)|(initial['IFF2']<<2)
 trace=[]
 for i in range(oracle.event_count()):
  t=(U*3)();oracle.get_event(i,t);trace.append(dict(kind=['MR','MW','PR','PW'][t[0]],address=t[1],value=t[2]))
 expected_mem=dict(memory)
 for e in trace:
  if e['kind']=='MW':expected_mem[f'{e["address"]:06x}']=e['value']
 return state,expected_mem,trace
def state_for(adl,scenario):
 vals=[0,1,0x0f,0x7f,0x80,0xff,0x55,0xaa]
 v=vals[scenario%8]; f=[0,0xff,1,0x40,0x80,0x04,0x10,0x93][scenario%8]
 addr=[0x234560,0x00ffff,0x010000,0xffffff,0x7fffff,0x800000,0x120000,0x12fffe][scenario%8]
 s=dict(zip(FIELDS,[v<<8|f,0x123400|v,0x345680,addr,0xa5d7,0xabcdef,0x765432,0x456789,addr,addr,addr,0x120100,0x80,0xfe,scenario%2,(scenario//2)%2,scenario%3,0,adl,0x7b,0,addr&65535]))
 s['I']=[0,0x7f,0x80,0xff,0x1234,0xffff,0x55aa,0xaa55][scenario%8]
 s['R']=[0,0x7e,0x7f,0x80,0xfe,0xff,0x55,0xaa][scenario%8]
 if not adl:s['PC']=0x0100
 return s
def make_case(entry,adl,suffix,scenario):
 s=state_for(adl,scenario); data_long=adl if suffix is None else suffix in (0x49,0x5b); imm_long=adl if suffix is None else suffix in (0x52,0x5b)
 head=list(entry['head']); space=entry['space'];op=entry['opcode']
 disp=[0,1,0x7f,0x80,0xff,0xfe,2,0x81][scenario%8]
 if space in ('DDCB','FDCB'):head[2]=disp
 code=([suffix] if suffix is not None else [])+head
 # Obtain exact length from independent disassembler for each suffix/mode.
 _,n=decode(code,adl)
 if n<len(code):raise ValueError((entry,code,n))
 operand_bytes=n-len(code)
 if operand_bytes:
  if space in ('DD','FD'):
   if op in (0x21,0x22,0x2a):
    value=[0,1,0xffff,0x10000,0x7fffff,0x800000,0xfffffe,0xffffff][scenario%8] if op==0x21 else 0x23ffff
    tail=[(value>>(8*i))&255 for i in range(operand_bytes)]
   elif op in (0x26,0x2e):tail=[[0,1,15,127,128,255,85,170][scenario%8]]
   else:tail=[disp]+([s['AF']>>8] if operand_bytes>1 else [])
  elif space=='ED':
   if op in [0x43,0x4b,0x53,0x5b,0x63,0x6b,0x73,0x7b]:tail=[0xff,0xff,0x23][:operand_bytes]
   elif op in [0x02,0x03,0x12,0x13,0x22,0x23,0x32,0x33,0x54,0x55,0x65,0x66]:tail=[disp]
   else:tail=[s['AF']>>8]
  elif operand_bytes>1:
   value=[0,1,0xffff,0x10000,0x7fffff,0x800000,0xfffffe,0xffffff][scenario%8] if space=='BASE' and op in (1,0x11,0x21,0x31) else 0x23ffff
   tail=[(value>>(8*i))&255 for i in range(operand_bytes)]
  else:tail=[disp if op in (0x10,0x18,0x20,0x28,0x30,0x38) else s['AF']>>8]
  assert len(tail)==operand_bytes,(entry,operand_bytes,tail)
  code+=tail
 if space=='ED' and op in ED_BLOCK:
  s['BC']=0x0202 if op in IO_BLOCK else 2
  s['DE']=0x345680 # avoid source/destination alias in repeat tests
  s['HL']=0x234560 if scenario<6 else 0x00ffff
 memory={}
 def mapped(a,long=data_long):return (a&0xffffff) if long else (s['MBASE']<<16)|(a&65535)
 for reg in ['BC','DE','HL','IX','IY']:
  for d in range(-3,5):memory[f'{mapped(s[reg]+d):06x}']=(scenario*29+d*17)&255
  if reg in ['IX','IY']:
   for d in range(3):memory[f'{mapped(s[reg]+(disp if disp<128 else disp-256)+d):06x}']=(0x81+d*0x31+scenario)&255
 for long,sp in [(False,s['SPS']),(True,s['SPL'])]:
  for d in range(-5,7):memory[f'{mapped(sp+d,long):06x}']=[0x34,0x12,0x56,0,0x78,0x9a][d%6]
 # Mixed-mode RET consumes a mode marker; use meaningful ADL=0/1 rather than arbitrary bits.
 if entry['mnemonic'] in ('RET','RETI','RETN') and suffix is not None:
  memory[f'{s["SPL"]&0xffffff:06x}']=adl
 for i in range(4):memory[f'{mapped(0x23ffff+i):06x}']=(0x12+0x23*i+scenario)&255
 pcphys=s['PC'] if adl else (s['MBASE']<<16)|s['PC']
 for i,v in enumerate(code):memory[f'{((pcphys+i)&0xffffff) if adl else ((s["MBASE"]<<16)|((s["PC"]+i)&65535)):06x}']=v
 key=f'{entry["key"]}_a{adl}_{"native" if suffix is None else f"p{suffix:02x}"}_s{scenario}'
 mask={k:0xffffff for k in FIELDS};mask.update(AF=0xffd7,AF2=0xffd7,R=0)
 notes=[]
 if space=='ED' and op in (0x57,0x5f):notes.append('UM0077 correction: PV=IFF2; pinned CEmu uses IFF1')
 if entry['mnemonic']=='BIT':mask['AF']&=~0x84;notes.append('BIT S/PV unspecified by UM0077')
 if space=='ED' and op==0x5f:
  mask['R']=0xff;notes.append('R normalized from CEmu internal rotated representation; LD A,R checked including all defined flags')
 if entry['mnemonic'] in { 'INI','IND','INIR','INDR','INI2','IND2','INI2R','IND2R','INIM','INDM','INIMR','INDMR','INIRX','INDRX','OUTI','OUTD','OTIR','OTDR','OUTI2','OUTD2','OTI2R','OTD2R','OTIM','OTDM','OTIMR','OTDMR','OTIRX','OTDRX'}:
  mask['AF']&=~0x95;notes.append('block I/O S/H/PV/C unspecified; masked conservatively')
 return dict(id=key,instruction=entry['key'],assembly=decode(code,adl)[0],code=code,steps=1,events={},io_seed=0x5a,initial=s,memory=memory,mask=mask,notes=notes,coverage='native' if suffix is None else 'size_prefix_probe')
def write_text(f,case,state,memory):
 f.write(case['id']+'\n')
 f.write(' '.join(f'{state[k]:04x}' if k in ('AF','AF2') else f'{state[k]:06x}' for k in FIELDS[:12])+'\n')
 f.write(f'{state["I"]:04x} {state["R"]:02x} '+ ' '.join(str(state[k]) for k in ['IFF1','IFF2','IM','HALTED'])+' 0\n')
 f.write(f'{state["ADL"]} {state["MBASE"]:02x} {state["MADL"]} {state["SPS"]:04x}\n')
 for a,v in sorted(memory.items()):f.write(f'{a} {v:02x} -1\n')
 f.write('-1\n\n')
def main():
 cat=catalog();(ROOT/'opcode_catalog.json').write_text(json.dumps(cat,indent=2)+'\n')
 rejected=[];counts={};casecount=0;nativecounts={};groups={}
 with (ROOT/'tests.in').open('w') as fi,(ROOT/'tests.expected').open('w') as fe,(ROOT/'cases.jsonl').open('w') as fj,(ROOT/'events.expected.jsonl').open('w') as ft:
  for e in cat:
   count=0
   for adl in (0,1):
    for suffix in SUFFIX:
     # Every native encoding gets eight complementary flag/data conditions.
     for scenario in range(8 if suffix is None else 2):
      c=make_case(e,adl,suffix,scenario)
      try:s,m,t=execute(c['initial'],c['memory'])
      except RuntimeError as err:
       rejected.append(dict(id=c['id'],reason=str(err)));continue
      write_text(fi,c,c['initial'],c['memory']);write_text(fe,c,s,m)
      fj.write(json.dumps(c,separators=(',',':'))+'\n');ft.write(json.dumps(dict(id=c['id'],events=t),separators=(',',':'))+'\n')
      count+=1;casecount+=1
      if suffix is None:nativecounts[e['key']]=nativecounts.get(e['key'],0)+1
   counts[e['key']]=count;groups[e['mnemonic']]=groups.get(e['mnemonic'],0)+count
   if len(counts)%100==0:print('generated',len(counts),'encodings;',casecount,'cases',flush=True)
 # Stateful external-event cases use full programs and boundary-scheduled IRQ/NMI.
  special=[]
  for adl in (0,1):
   for im in (0,1,2):
    for madl in (0,1):
     for kind,label in [(1,'NMI'),(2,'IRQ')]:
      s=state_for(adl,0);s.update(IFF1=1,IFF2=1,IM=im,MADL=madl,I=0x80)
      memory={f'{a:06x}':v for a,v in [(0x8000|0x5a,0x34),(0x8000|0x5b,0x12),(0x8000|0x5c,0x56),(0x7b805a,0x34),(0x7b805b,0x12),(0x7b805c,0x56)]}
      c=dict(id=f'event_{label}_a{adl}_im{im}_madl{madl}',instruction=label,assembly=label,code=[],steps=1,events={0:kind},io_seed=0x5a,initial=s,memory=memory,mask=dict(AF=0xffd7,AF2=0xffd7,R=0),notes=['Reference-model interrupt acknowledgement policy; IM0 vector is supplied externally'],coverage='external_event')
      special.append(c)
   for kind,label in [(0,'EI_NOP'),(2,'EI_NOP_IRQ'),(2,'EI_IRQ_PENDING'),(1,'HALT_NMI'),(2,'HALT_IRQ')]:
    s=state_for(adl,0);s.update(IFF1=0 if label.startswith('EI') else 1,IFF2=1,IM=1)
    code=[0xfb,0,0] if label.startswith('EI') else [0x76,0]
    pc=s['PC'] if adl else (s['MBASE']<<16)|s['PC'];memory={f'{pc+i:06x}':v for i,v in enumerate(code)}
    c=dict(id=f'sequence_{label}_a{adl}',instruction=label,assembly=label,code=code,steps=3 if label.startswith('EI') else 2,events=({1:kind} if label=='EI_IRQ_PENDING' else {2:kind} if label.startswith('EI') and kind else {1:kind} if kind else {}),io_seed=0x5a,initial=s,memory=memory,mask=dict(AF=0xffd7,AF2=0xffd7,R=0),notes=['Event indices count complete instructions, not clock cycles'],coverage='external_event');special.append(c)
  for c in special:
   s,m,t=execute(c['initial'],c['memory'],c['steps'],c['events'],c['io_seed']);write_text(fi,c,c['initial'],c['memory']);write_text(fe,c,s,m);fj.write(json.dumps(c,separators=(',',':'))+'\n');ft.write(json.dumps(dict(id=c['id'],events=t),separators=(',',':'))+'\n');casecount+=1
 with (ROOT/'coverage.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['encoding','mnemonic','assembly','native_cases','all_cases','status'])
  for e in cat:w.writerow([e['key'],e['mnemonic'],e['assembly'],nativecounts.get(e['key'],0),counts[e['key']],'generated' if nativecounts.get(e['key'])==16 else 'GAP'])
 summary=dict(format='EZ80-FUSE-ADL-v2',total_cases=casecount,encoding_count=len(cat),mnemonics=groups,external_event_cases=len(special),native_cases=sum(nativecounts.values()),prefix_probe_cases=sum(counts.values())-sum(nativecounts.values()),native_encoding_gaps=[e['key'] for e in cat if nativecounts.get(e['key'])!=16],oracle_rejected=rejected,validation='reference-generated, not eZ80X RTL PASS or silicon-certified')
 (ROOT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({k:v for k,v in summary.items() if k not in ('oracle_rejected','mnemonics')},indent=2))
if __name__=='__main__':main()
