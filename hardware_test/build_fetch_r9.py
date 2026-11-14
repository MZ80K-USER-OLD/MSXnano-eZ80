from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent.parent;src=(root/'hardware_test/build_data_r3.py').read_text()
exec(src[:src.index("label('START')")],globals());r=root/'hardware_test'
rows=[]
def patch_a(v):
 emit(0x3e,0)
 if isinstance(v,tuple):bytefix.append((len(b)-1,v[0],0,v[1]))
 else:b[-1]=v

def byte_verify(addr,v):
 loadpair('HL',addr);indir('HL',False)
 if not isinstance(v,tuple):check(v,addr);return
 sa('DIAG_ACT');patch_a(v);sa('DIAG_EXP');ref([0x21],'DIAG_ACT');emit(0xbe)
 ok='PAYLOAD_BYTE_OK_'+str(len(b));ref([0xca],ok);address_context(addr);ref([0xc3],'FAIL');label(ok)

def payload(base,instructions,results,setup=None,acc_check=None,skip_fetch_offsets=()):
 n=len(rows)+1;ret=f'RETURN_{n}';data=[];fetch=[]
 for inst in instructions+[[0x40,0xc3,(ret,0),(ret,1)]]:
  for j,v in enumerate(inst):
   data.append(v)
   if j==0 or (all(isinstance(x,int) and x in (0x40,0x49,0x52,0x5b,0xdd,0xfd,0xed,0xcb) for x in inst[:j])):
    fetch.append((base+len(data)-1,v))
 fetch=[(a,v) for a,v in fetch if a-base not in skip_fetch_offsets]
 stage(str(n))
 # Load and independently read back all code bytes, including patched return operands.
 for i,v in enumerate(data):loadpair('HL',base+i);patch_a(v);indir('HL',True)
 for i,v in enumerate(data):byte_verify(base+i,v)
 if setup:setup()
 emit(0x5b,0xc3,base&255,(base>>8)&255,base>>16)
 label(ret)
 if acc_check is not None:check(acc_check)
 for addr,val in results:
  if isinstance(addr,str):la(addr);check(val,(addr,0))
  else:readcheck(addr,val)
 emit(0x3a,0xff,0xff);check(('SLOT_SAVED',0),0xffff)
 rows.append(dict(case=n,base=base,data=data,fetch=fetch,return_label=ret,results=results))

label('START');emit(0xdd,0xe5,0xfd,0xe5,0xf3);ref([0xed,0x73],'SAVED_SPS')
for addr,val in [(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:emit(0x3a,addr,0,0xfe,val);ref([0xc2],'READY')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED');emit(0x3a,0xff,0xff);sa('SLOT_SAVED')
payload(0x02fffe,[[0x21,0x56,0x34,0x12],[0x22,0,1,6],[0x40,0x21,0xcd,0xab],[0x22,4,1,6],
 [0x52,0x11,0x78,0x56,0xa4],[0xed,0x53,8,1,6],[0x5b,0x21,0xef,0xcd,0xab],[0x22,12,1,6],[0x3e,0xa6],[0x32,16,1,6]],
 [(0x060100+i,v) for i,v in enumerate([0x56,0x34,0x12])]+[(0x060104+i,v) for i,v in enumerate([0xcd,0xab,0x12])]+[(0x060108+i,v) for i,v in enumerate([0x78,0x56,0x00])]+[(0x06010c+i,v) for i,v in enumerate([0xef,0xcd,0xab])]+[(0x060110,0xa6)],setup=lambda:loadpair('DE',0x0c0000))
payload(0x03ffff,[[0xdd,0x21,0,0x80,7],[0x3e,0x69],[0xdd,0x77,1],[0xdd,0x7e,1],[0x32,17,1,6]],[(0x078001,0x69),(0x060111,0x69)])
payload(0x04fffe,[[0x49,0xed,0x43,('LOW_PAIR',0),('LOW_PAIR',1)],[0x11,0x33,0x22,0x11],[0xed,0x53,18,1,6]],
 [('LOW_PAIR',0x34),('LOW_PAIR1',0x12),('LOW_PAIR2',0x0b)]+[(0x060112+i,v) for i,v in enumerate([0x33,0x22,0x11])],setup=lambda:loadpair('BC',0x0b1234))
payload(0x05ffff,[],[],setup=lambda:emit(0x3e,0x3c),acc_check=0x3c)
payload(0x07ffff,[[0xfd,0x21,0xff,0xff,1],[0x3e,0xd7],[0xfd,0x77,1],[0xfd,0x7e,1],[0x32,21,1,6]],[(0x020000,0xd7),(0x060115,0xd7)])
payload(0x08fffd,[[0xc3,0x10,0,9]]+[[0]]*15+[[0x3e,0x96],[0x32,22,1,6]],[(0x060116,0x96)],skip_fetch_offsets=range(4,19))
ref([0xed,0x73],'SPS_SNAPSHOT')
for i in range(2):la('SPS_SNAPSHOT'+('' if not i else '1'));check(('SAVED_SPS'+('' if not i else '1'),0),('SPS_SNAPSHOT',i))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('MSG_READY');emit(*b'EZ80F9 R9: READY - use /RUN\r\n$')
footer=src[src.index("label('SUBROUTINE')"):].replace('EZ80D3','EZ80F9').replace('`define R3_','`define F9_').replace(' R3',' R9')
footer=footer.replace('for at,name,off,i in bytefix:',"label('SLOT_SAVED');emit(0)\nlabel('LOW_PAIR');emit(0,0,0);labels['LOW_PAIR1']=labels['LOW_PAIR']+1;labels['LOW_PAIR2']=labels['LOW_PAIR']+2\nfor at,name,off,i in bytefix:")
exec(footer,globals())
for row in rows:
 row['data']=[((labels[v[0]]>>(8*v[1]))&255) if isinstance(v,tuple) else v for v in row['data']]
 row['fetch']=[dict(address=a,byte=v) for a,v in row['fetch']]
 row['return_pc']=labels[row['return_label']]
(r/'EZ80F9.json').write_text(json.dumps(dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),labels=labels,cases=rows,stage=5,requires_R9=True,ADL_CALL_RET_required=False),indent=2)+'\n')
# Simulation ROM expectations are derived from instruction boundaries, not RTL output.
lines=['expected_count=0;']
for row in rows:
 for v in row['fetch']:lines.append(f"expected_addr[expected_count]=24'h{v['address']:06x};expected_byte[expected_count]=8'h{v['byte']:02x};expected_count=expected_count+1;")
 lines.append(f"return_pc[{row['case']-1}]=16'h{row['return_pc']:04x};")
(root/'sim/fetch_plan.vh').write_text('\n'.join(lines)+'\n')
