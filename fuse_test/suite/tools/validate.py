"""Structural checks + separately coded specification checks; never claims RTL PASS."""
from pathlib import Path
import sys,json,collections
sys.path.insert(0,str(Path(__file__).parent))
import generate as g
ROOT=g.ROOT
def blocks(path):
 with open(path) as f:
  while True:
   name=f.readline().strip()
   if not name:
    if not f.readline():return
    raise ValueError('unexpected blank')
   regs=f.readline().split();q=f.readline().split();mode=f.readline().split()
   assert len(regs)==12 and len(q)==7 and len(mode)==4
   state=dict(zip(g.FIELDS[:12],map(lambda v:int(v,16),regs)))
   state.update(I=int(q[0],16),R=int(q[1],16),IFF1=int(q[2]),IFF2=int(q[3]),IM=int(q[4]),HALTED=int(q[5]),ADL=int(mode[0]),MBASE=int(mode[1],16),MADL=int(mode[2]),SPS=int(mode[3],16))
   assert q[6]=='0'
   memory={}
   for row in f:
    if row.strip()=='-1':break
    z=row.split();assert len(z)==3 and z[-1]=='-1'
    a=int(z[0],16);v=int(z[1],16);assert 0<=a<=0xffffff and 0<=v<=255 and z[0] not in memory
    memory[z[0]]=v
   assert f.readline()=='\n'
   yield dict(id=name,state=state,memory=memory)
def audit_catalog():
 # Independently transcribed valid binary cells of UM0077 Tables 106-112.
 ed='00 01 02 03 04 07 08 09 0c 0f 10 11 12 13 14 17 18 19 1c 1f 20 21 22 23 24 27 28 29 2c 2f 31 32 33 34 37 38 39 3c 3e 3f 40 41 42 43 44 45 46 47 48 49 4a 4b 4c 4d 4f 50 51 52 53 54 55 56 57 58 59 5a 5b 5c 5e 5f 60 61 62 63 64 65 66 67 68 69 6a 6b 6c 6d 6e 6f 72 73 74 76 78 79 7a 7b 7c 7d 7e 82 83 84 8a 8b 8c 92 93 94 9a 9b 9c a0 a1 a2 a3 a4 a8 a9 aa ab ac b0 b1 b2 b3 b4 b8 b9 ba bb bc c2 c3 c7 ca cb d7'
 dd='07 09 0f 17 19 1f 21 22 23 24 25 26 27 29 2a 2b 2c 2d 2e 2f 31 34 35 36 37 39 3e 3f 44 45 46 4c 4d 4e 54 55 56 5c 5d 5e 60 61 62 63 64 65 66 67 68 69 6a 6b 6c 6d 6e 6f 70 71 72 73 74 75 77 7c 7d 7e 84 85 86 8c 8d 8e 94 95 96 9c 9d 9e a4 a5 a6 ac ad ae b4 b5 b6 bc bd be e1 e3 e5 e9 f9'
 expected={'BASE':set(range(256))-{0x40,0x49,0x52,0x5b,0xcb,0xdd,0xed,0xfd},'CB':set(range(256))-set(range(0x30,0x38)),'ED':set(int(x,16) for x in ed.split()),'DD':set(int(x,16) for x in dd.split()),'FD':set(int(x,16) for x in dd.split()),'DDCB':{x for x in range(256) if x&7==6 and x!=0x36},'FDCB':{x for x in range(256) if x&7==6 and x!=0x36}}
 actual=collections.defaultdict(set)
 for e in g.catalog():actual[e['space']].add(e['opcode'])
 for space in expected:assert actual[space]==expected[space],(space,expected[space]-actual[space],actual[space]-expected[space])
 return {k:len(v) for k,v in expected.items()}
def alu(a,b,c,op):
 if op in (0,1,2,3,7):
  sub=op in (2,3,7);carry=c if op in (1,3) else 0
  raw=a-b-carry if sub else a+b+carry;r=raw&255
  h=((a&15)-(b&15)-carry<0) if sub else ((a&15)+(b&15)+carry>15)
  overflow=((a^b)&(a^r)&128)!=0 if sub else ((~(a^b)&(a^r)&128)!=0)
  f=(r&128)|(64 if r==0 else 0)|(16 if h else 0)|(4 if overflow else 0)|(2 if sub else 0)|(1 if raw<0 or raw>255 else 0)
  return (a if op==7 else r),f
 r=[a&b,a^b,a|b][op-4];return r,(r&128)|(64 if not r else 0)|(16 if op==4 else 0)|(4 if r.bit_count()%2==0 else 0)
def independent_checks():
 count=0
 for op in range(8):
  for a in (0,1,15,127,128,255):
   for b in (0,1,15,127,128,255):
    for carry in (0,1):
     s=g.state_for(1,0);s.update(AF=a<<8|carry,BC=b<<8|0x12)
     out,_,_=g.execute(s,{'120100':0x80+8*op})
     av,f=alu(a,b,carry,op)
     assert out['AF']&0xffd7==av<<8|f,(op,a,b,carry,out['AF'],av,f)
     count+=1
 for value in (0,0x7e,0x7f,0x80,0xfe,0xff):
  for iff1 in (0,1):
   for iff2 in (0,1):
    for carry in (0,1):
     for op in (0x57,0x5f):
      s=g.state_for(1,0);s.update(R=value,I=value,IFF1=iff1,IFF2=iff2,AF=carry)
      out,_,_=g.execute(s,{'120100':0xed,'120101':op})
      a=value if op==0x57 else (value&128)|((value+2)&127)
      f=(a&128)|(64 if not a else 0)|(iff2<<2)|carry
      assert out['AF']&0xffd7==a<<8|f
      count+=1
 for adl in (0,1):
  for vector in range(0,64,8):
   s=g.state_for(adl,0);pc=s['PC'] if adl else (s['MBASE']<<16)|s['PC'];out,m,t=g.execute(s,{f'{pc:06x}':0xc7|vector})
   assert out['PC']==vector and out['ADL']==adl
   writes=[e for e in t if e['kind']=='MW'];assert len(writes)==2+adl
   pushed=sum(e['value']<<(8*i) for i,e in enumerate(reversed(writes)))
   assert pushed==(s['PC']+1)&(0xffffff if adl else 65535)
   count+=1
 for adl in (0,1):
  for op in (0x00,0x01,0x4c):
   s=g.state_for(adl,0);s.update(BC=0x1234,AF=0x8100)
   pc=s['PC'] if adl else (s['MBASE']<<16)|s['PC'];mem={f'{pc:06x}':0xed,f'{pc+1:06x}':op,f'{pc+2:06x}':0x9a};out,m,t=g.execute(s,mem)
   if op==0x4c:assert out['BC']==0x12*0x34
   else:
    io=[e for e in t if e['kind'] in ('PR','PW')];assert len(io)==1 and io[0]['address']==0x9a
   count+=1
 return count
def main():
 counts=audit_catalog();checks=independent_checks();n=0;ids=set();native=collections.Counter();cases=iter((ROOT/'cases.jsonl').open());events=iter((ROOT/'events.expected.jsonl').open())
 import itertools
 for a,b,c,t in itertools.zip_longest(blocks(ROOT/'tests.in'),blocks(ROOT/'tests.expected'),cases,events):
  assert a is not None and b is not None and c is not None and t is not None
  c=json.loads(c);t=json.loads(t);assert a['id']==b['id']==c['id']==t['id'] and a['id'] not in ids;ids.add(a['id'])
  assert a['state']==c['initial'] and a['memory']==c['memory']
  if c['coverage']=='native':native[c['instruction']]+=1
  expected=dict(a['memory'])
  for e in t['events']:
   assert e['kind'] in ('MR','MW','PR','PW') and 0<=e['value']<256
   assert 0<=e['address']<(0x10000 if e['kind'][0]=='P' else 0x1000000)
   if e['kind']=='MW':expected[f'{e["address"]:06x}']=e['value']
  assert expected==b['memory'];n+=1
 assert len(native)==sum(counts.values()) and all(v==16 for v in native.values())
 summary=json.loads((ROOT/'summary.json').read_text());assert n==summary['total_cases'] and not summary['oracle_rejected']
 result=dict(status='PASS',structural_cases=n,independent_spec_checks=checks,opcode_map_cells=counts,missing_native_encodings=0,scope='data/oracle checks, no RTL or silicon execution')
 (ROOT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
