from pathlib import Path
import json,zlib,hashlib
r=Path(__file__).resolve().parent;base=(r/'build_data_r3.py').read_text();exec(base[:base.index("label('START')")])
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5);ref([0xed,0x73],'SAVED_SPS')
for a,v in[(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:emit(0x3a,a,0,0xfe,v);ref([0xc2],'READY')
# Print only while Z80, MBASE0, extensions locked. DOS may EI; DI follows.
def printmsg(n):ref([0x11],n);emit(0xfb,0x0e,9,0xcd,5,0,0xf3)
printmsg('MSG_START')
# No extension enabled yet: test the ordinary DOS-program memory path.
emit(0x3e,0x31);sa('LOCAL_CELL');la('LOCAL_CELL');sa('LOCAL_VALUE');emit(0xfe,0x31);ref([0xca],'LOCAL_OK');ref([0x21],'FAIL_COUNT');emit(0x34);label('LOCAL_OK')
ref([0x21],'LOCAL_HEX');la('LOCAL_VALUE');ref([0xcd],'HEX_BYTE');printmsg('MSG_LOCAL')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
for sel,val in [(0xfb,2),(0xfc,0xfd)]:gate(sel);emit(0xed,0x78,0xfe,val);ref([0xc2],'NOT_READY')
gate(0)
rows=[]
for addr in(0x010100,0x070100,0x07fffe):
 for writer,expected in [('A',0x31),('I',0xce)]:
  idx=len(rows);gate(0xa5);gate(0x5a)
  loadpair('HL',addr);emit(0x3e,expected)
  if writer=='A':emit(0x5b,0x32,*addr.to_bytes(3,'little'))
  else:indir('HL',True)
  for j in range(4):
   if j<2:emit(0x5b,0x3a,*addr.to_bytes(3,'little'))
   else:loadpair('HL',addr);indir('HL',False)
   sa(f'V{idx}_{j}')
  # LIS absolute address: store all three bytes of HL into ordinary MSX RAM.
  ref([0x49,0x22],f'H{idx}_0')
  for k in range(8):gate(0xf0+k);emit(0xed,0x78);sa(f'T{idx}_{k}')
  gate(0)
  checks=[(f'V{idx}_{j}',expected)for j in range(4)]+[(f'H{idx}_{j}',(addr>>(8*j))&255)for j in range(3)]
  phy=0x640000+addr
  checks += [(f'T{idx}_{j}',v)for j,v in enumerate([expected,*phy.to_bytes(3,'little'),expected,*phy.to_bytes(3,'little')])]
  for n,v in checks:
   la(n);emit(0xfe,v);ok='OK_'+str(len(b));ref([0xca],ok);ref([0x21],'FAIL_COUNT');emit(0x34);label(ok)
   ref([0x21],'HEX_'+n);la(n);ref([0xcd],'HEX_BYTE')
  printmsg('ROW_'+str(idx));rows.append(dict(index=idx,writer=writer,address=f'{addr:06X}',expected=f'{expected:02X}'))
la('FAIL_COUNT');emit(0xb7);ref([0xc2],'BAD');emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('BAD');emit(0x3e,2);sa('STATUS');ref([0x11],'MSG_FAIL');ref([0xc3],'FINISH')
label('READY');emit(0x3e,4);sa('STATUS');ref([0x11],'MSG_READY');ref([0xc3],'FINISH')
label('NOT_READY');emit(0x3e,5);sa('STATUS');ref([0x11],'MSG_NOT_READY');ref([0xc3],'FINISH')
label('UNSUPPORTED');emit(0x3e,3);sa('STATUS');ref([0x11],'MSG_UNSUPPORTED')
label('FINISH');emit(0xf3,0xed,0x56,0xd5);gate(0);emit(0xd1,0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)
# Hex output formatting: ordinary Z80 helper, extensions locked.
exec(base[base.index("label('HEX_BYTE')"):base.index("label('MSG_PASS')")])
for n,s in [('MSG_START','EZ80MR3 R21.2 START'),('MSG_PASS','EZ80MR3 R21.2: PASS'),('MSG_FAIL','EZ80MR3 R21.2: FAIL (see rows)'),('MSG_READY','EZ80MR3 R21.2: READY (use /RUN)'),('MSG_NOT_READY','EZ80MR3 R21.2: NOT READY'),('MSG_UNSUPPORTED','EZ80MR3 R21.2: UNSUPPORTED')]:label(n);emit(*(s+'\r\n$').encode())
label('MSG_LOCAL');emit(*b'LOCAL EXP=31 ACT=');label('LOCAL_HEX');emit(*b'00\r\n$')
for row in rows:
 i=row['index'];label('ROW_'+str(i));emit(*(f"{row['writer']} {row['address']} E{row['expected']} A1=".encode()))
 for j in range(4):
  if j==1:emit(*b' A2=')
  if j==2:emit(*b'\r\nI1=')
  if j==3:emit(*b' I2=')
  label(f'HEX_V{i}_{j}');emit(*b'00')
 emit(*b' HL=')
 for j in(2,1,0):label(f'HEX_H{i}_{j}');emit(*b'00')
 emit(*b'\r\nW=')
 for j in (3,2,1):label(f'HEX_T{i}_{j}');emit(*b'00')
 emit(ord('/'));label(f'HEX_T{i}_0');emit(*b'00 R=')
 for j in (7,6,5):label(f'HEX_T{i}_{j}');emit(*b'00')
 emit(ord('/'));label(f'HEX_T{i}_4');emit(*b'00\r\n$')
label('STATUS');emit(0);label('FAIL_COUNT');emit(0);label('LOCAL_CELL');emit(0);label('LOCAL_VALUE');emit(0);label('SAVED_SPS');emit(0,0)
# Guard macro retained for reuse of the actual-COM simulation harness.
label('GUARD');emit(0xa6);label('FAIL_STAGE');emit(ord('M'))
for row in rows:
 i=row['index']
 for j in range(4):label(f'V{i}_{j}');emit(0)
 for j in range(3):label(f'H{i}_{j}');emit(0)
 for j in range(8):label(f'T{i}_{j}');emit(0)
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)+0x100<0x6000
name='EZ80MR3'
(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{x:02x}\n'for x in b));(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n")
(r/(name+'.json')).write_text(json.dumps(dict(name=name,bytes=len(b),crc32=f'{zlib.crc32(b):08X}',sha256=hashlib.sha256(b).hexdigest(),labels=labels,rows=rows),indent=2)+'\n')
(r/(name+'.asm')).write_text('ORG 0100h\n'+'\n'.join(f'{n} EQU 0{v:04X}h'for n,v in labels.items())+'\n'+'\n'.join(' DEFB '+','.join(f'0{v:02X}h'for v in b[a:a+n])+f' ; {0x100+a:04X}'for a,n,_ in listing)+'\n')
print(name,len(b),f'{zlib.crc32(b):08X}')
