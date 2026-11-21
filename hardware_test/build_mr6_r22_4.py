"""R22.4: history-address matrix and controller/bridge/CPU observations.
No DOS/BIOS calls with extensions enabled. DOS may EI; DI immediately on return.
"""
from pathlib import Path
import json,zlib,hashlib,sys
MATRIX="--matrix" in sys.argv
NAME="EZ80MX6" if MATRIX else "EZ80MR6"
r=Path(__file__).resolve().parent
base=(r/'build_data_r3.py').read_text();exec(base[:base.index("label('START')")])
def printmsg(n):ref([0x11],n);emit(0xfb,0x0e,9,0xcd,5,0,0xf3)
def unlock():gate(0xa5);gate(0x5a)
label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5);ref([0xed,0x73],'SAVED_SPS')
for a,v in [(0x80,5),(0x81,32),(0x82,47),(0x83,82),(0x84,85),(0x85,78)]:
 emit(0x3a,a,0,0xfe,v);ref([0xc2],'READY')
printmsg('MSG_START')
emit(0x3e,0x31);sa('LOCAL_CELL');la('LOCAL_CELL');sa('LOCAL_VALUE')
ref([0x21],'LOCAL_HEX');la('LOCAL_VALUE');ref([0xcd],'HEX_BYTE');printmsg('MSG_LOCAL')
la('LOCAL_VALUE');emit(0xfe,0x31);ref([0xc2],'LOCAL_BAD')
unlock();emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
for sel,val in [(0xfb,3),(0xfc,0xfc)]:gate(sel);emit(0xed,0x78,0xfe,val);ref([0xc2],'NOT_READY')
for k,sel in enumerate((0xfd,0xfe)):gate(sel);emit(0xed,0x78);sa('LINK'+str(k))
gate(0)
for k in range(2):ref([0x21],'LINK_HEX'+str(k));la('LINK'+str(k));ref([0xcd],'HEX_BYTE')
printmsg('MSG_LINK')
for k,val in enumerate((0x55,0xaa)):la('LINK'+str(k));emit(0xfe,val);ref([0xc2],'LINK_BAD')
unlock();gate(0xd8)
for sel,val in [(0xee,0x5b),(0xef,0xa4)]:gate(sel);emit(0xed,0x78,0xfe,val);ref([0xc2],'NOT_READY')
gate(0)
rows=[]
addresses=(0x010100,0x010101,0x010102,0x010103,0x070100,0x07fffe,0x07ffff,0x080000,0x0a6000) if MATRIX else (0x010100,)
for addr in addresses:
 for writer,expected in [('G',0x31),('B',0xce)]:
  i=len(rows);phy=0x640000+addr
  printmsg('BEGIN_'+str(i));unlock();loadpair('HL',addr);emit(0x3e,expected)
  if writer=='G':emit(0x5b,0x32,*addr.to_bytes(3,'little'))
  else:indir('HL',True)
  if writer=='G':gate(0);printmsg('GAP_'+str(i));unlock()
  for j in range(4):
   if j<2:emit(0x5b,0x3a,*addr.to_bytes(3,'little'))
   else:loadpair('HL',addr);indir('HL',False)
   sa(f'V{i}_{j}')
  ref([0x49,0x22],f'H{i}_0')
  for k in range(8):gate(0xf0+k);emit(0xed,0x78);sa(f'T{i}_{k}')
  gate(0xd8)
  for k in range(12):gate(0xe2+k);emit(0xed,0x78);sa(f'P{i}_{k}')
  gate(0)
  checks=[(f'V{i}_{j}',expected)for j in range(4)]+[(f'H{i}_{j}',(addr>>(8*j))&255)for j in range(3)]
  checks += [(f'T{i}_{j}',v)for j,v in enumerate([expected,*phy.to_bytes(3,'little'),expected,*phy.to_bytes(3,'little')])]
  mask=15^(1<<(phy&3));control=((phy>>21)<<6)|((phy&3)<<4)|mask
  # DQ early/late are observations, not independent pass/fail requirements.
  checks +=[(f'P{i}_{j}',expected)for j in range(4)]
  checks +=[(f'P{i}_{6+j}',v)for j,v in enumerate(phy.to_bytes(3,'little'))]
  checks +=[(f'P{i}_9',control),(f'P{i}_10',0x7f),(f'P{i}_11',(phy>>13)&255)]
  for n,v in checks:
   la(n);sa('CURRENT_ACT');emit(0xfe,v);ok='OK_'+str(len(b));ref([0xca],ok)
   la('FAIL_COUNT');emit(0xb7);known='KNOWN_'+str(len(b));ref([0xc2],known)
   emit(0x3e,v);sa('FIRST_EXP');la('CURRENT_ACT');sa('FIRST_ACT')
   for k in range(3):emit(0x3e,(addr>>(8*k))&255);sa('FIRST_ADDR'+str(k))
   label(known);emit(0x3e,1);sa('FAIL_COUNT');label(ok)
  for family,count in [('V',4),('H',3),('T',8),('P',12)]:
   for j in range(count):ref([0x21],f'HEX_{family}{i}_{j}');la(f'{family}{i}_{j}');ref([0xcd],'HEX_BYTE')
  printmsg('ROW_'+str(i));rows.append(dict(index=i,writer=writer,address=f'{addr:06X}',expected=f'{expected:02X}',physical=f'{phy:06X}',control=f'{control:02X}'))
la('FAIL_COUNT');emit(0xb7);ref([0xc2],'BAD');emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
label('BAD')
for src,dst in [('FIRST_EXP','FAIL_EXP'),('FIRST_ACT','FAIL_ACT')]:ref([0x21],dst);la(src);ref([0xcd],'HEX_BYTE')
ref([0x21],'FAIL_ADDR')
for k in (2,1,0):la('FIRST_ADDR'+str(k));ref([0xcd],'HEX_BYTE')
emit(0x3e,2);sa('STATUS');ref([0x11],'MSG_FAIL');ref([0xc3],'FINISH')
for name,status in [('READY',4),('NOT_READY',5),('UNSUPPORTED',3),('LINK_BAD',6),('LOCAL_BAD',7)]:
 label(name);emit(0x3e,status);sa('STATUS');ref([0x11],'MSG_'+name);ref([0xc3],'FINISH')
label('FINISH');emit(0xf3,0xed,0x56,0xd5);gate(0);emit(0xd1,0xfb,0x0e,9,0xcd,5,0,0xf3,0xfd,0xe1,0xdd,0xe1,0xfb,0xc9)
exec(base[base.index("label('HEX_BYTE')"):base.index("label('MSG_PASS')")])
for n,t in [('START','START'),('PASS','PASS'),('READY','READY (use /RUN)'),('NOT_READY','NOT READY (requires R22.4)'),('UNSUPPORTED','UNSUPPORTED'),('LINK_BAD','TRACE LINK FAIL'),('LOCAL_BAD','LOCAL FAIL')]:
 label('MSG_'+n);emit(*(f'{NAME} R22.4: {t}\r\n$').encode())
label('MSG_FAIL');emit(*(NAME+' R22.4: FAIL\r\nADDR=').encode());label('FAIL_ADDR');emit(*b'000000 EXP=');label('FAIL_EXP');emit(*b'00 ACT=');label('FAIL_ACT');emit(*b'00 (see row fields)\r\n$')
label('MSG_LOCAL');emit(*b'LOCAL EXP=31 ACT=');label('LOCAL_HEX');emit(*b'00\r\n$')
label('MSG_LINK');emit(*b'LINK EXP=55/AA ACT=');label('LINK_HEX0');emit(*b'00/');label('LINK_HEX1');emit(*b'00\r\n$')
for row in rows:
 i=row['index'];a=row['address'];e=row['expected']
 label('BEGIN_'+str(i));emit(*(f'BEGIN {row["writer"]} ADDR={a} EXP={e}\r\n$').encode())
 if row['writer']=='G':label('GAP_'+str(i));emit(*(f'WRITE_DONE {a} (DOS gap)\r\n$').encode())
 label('ROW_'+str(i));emit(*(f'{row["writer"]} ADDR={a} EXP={e} A1=').encode())
 for j in range(4):
  if j:emit(*([' A2=',' I1=',' I2='][j-1].encode()))
  label(f'HEX_V{i}_{j}');emit(*b'00')
 emit(*b' HL=')
 for j in (2,1,0):label(f'HEX_H{i}_{j}');emit(*b'00')
 emit(*b'\r\nW=')
 for j in(3,2,1):label(f'HEX_T{i}_{j}');emit(*b'00')
 emit(ord('/'));label(f'HEX_T{i}_0');emit(*b'00 R=')
 for j in(7,6,5):label(f'HEX_T{i}_{j}');emit(*b'00')
 emit(ord('/'));label(f'HEX_T{i}_4');emit(*b'00')
 for j,title in [(0,'\r\nCAP='),(1,' CMD='),(2,' RAM='),(3,' RET='),(4,'\r\nDQ1='),(5,' DQ2=')]:
  emit(*title.encode());label(f'HEX_P{i}_{j}');emit(*b'00')
 emit(*b' WCAP=')
 for j in (8,7,6):label(f'HEX_P{i}_{j}');emit(*b'00')
 for j,title in [(9,'\r\nCTL='),(10,' VALID='),(11,' COL=')]:emit(*title.encode());label(f'HEX_P{i}_{j}');emit(*b'00')
 emit(*b'\r\n$')
for name in ['STATUS','FAIL_COUNT','LOCAL_CELL','LOCAL_VALUE','LINK0','LINK1','CURRENT_ACT','FIRST_EXP','FIRST_ACT','FIRST_ADDR0','FIRST_ADDR1','FIRST_ADDR2']:label(name);emit(0)
label('SAVED_SPS');emit(0,0);label('GUARD');emit(0xa6);label('FAIL_STAGE');emit(ord('M'))
for row in rows:
 i=row['index']
 for family,count in [('V',4),('H',3),('T',8),('P',12)]:
  for j in range(count):label(f'{family}{i}_{j}');emit(0)
for at,n in fix:b[at:at+2]=labels[n].to_bytes(2,'little')
assert len(b)+0x100<0xc000,(len(b),'must fit below DOS stack/BDOS')
name=NAME
(r/(name+'.COM')).write_bytes(b);(r/(name+'.hex')).write_text(''.join(f'{x:02x}\n'for x in b))
(r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in labels.items())+f"`define P2_COM_END 16'h{0xff+len(b):04x}\n`define P2_NORMAL_DOS_CALLS {4+len(rows)*2+len(rows)//2}\n")
(r/(name+'.asm')).write_text('; Generated resolved bytes. ORG 0100h. See JSON for labels.\nORG 0100h\n'+''.join('DEFB '+','.join(f'{v:02X}h' for v in b[j:j+16])+'\n' for j in range(0,len(b),16)))
(r/(name+'.json')).write_text(json.dumps(dict(name=name,bytes=len(b),crc32=f'{zlib.crc32(b):08X}',sha256=hashlib.sha256(b).hexdigest(),labels=labels,rows=rows,normal_DOS_calls=4+len(rows)*2+len(rows)//2,requires_R22_4=True),indent=2)+'\n')
print(name,len(b),f'{zlib.crc32(b):08X}',len(rows),'rows')
