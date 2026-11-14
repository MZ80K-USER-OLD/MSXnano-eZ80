"""R15.1 software-only diagnostics; no FPGA source changes."""
from pathlib import Path
import json,re,hashlib,zlib
r=Path(__file__).resolve().parent.parent;h=r/'hardware_test'
def hash(b):return hashlib.sha256(b).hexdigest()
def gate(v):return bytes([1,0xe7,0xe7,0x3e,v,0xed,0x79])
def print_code(message,restore_gate):
 # Called in Z80 mode only. Preserve registers and SPS, lock before DOS,
 # allow DOS to EI, then DI immediately and normalize IM1 before reopening.
 return bytes.fromhex('F5 C5 D5 E5 DD E5 FD E5')+gate(0)+bytes([0x11,message&255,message>>8,0xfb,0x0e,9,0xcd,5,0,0xf3,0xed,0x56])+(gate(0xa5)+gate(0x5a) if restore_gate else b'')+bytes.fromhex('FD E1 DD E1 E1 D1 C1 F1')
def dump(name,b,meta,header):
 (h/(name+'.COM')).write_bytes(b);(h/(name+'.hex')).write_text(''.join(f'{v:02x}\n' for v in b))
 (h/(name+'.json')).write_text(json.dumps(meta,indent=2)+'\n')
 (h/(name+'.asm')).write_text('; R15.1 diagnostic, resolved bytes\nORG 0100h\n'+''.join(' DEFB '+','.join(f'0{v:02X}h' for v in b[i:i+16])+f' ; {0x100+i:04X}\n' for i in range(0,len(b),16)))
 (h/(name+'.vh')).write_text(header)
# Trace the unchanged TST payload with one numbered marker before each case.
old=(h/'EZ80TST.COM').read_bytes();m=json.loads((h/'EZ80TST.json').read_text());assert len(old)==12968
b=bytearray(old.replace(b'EZ80TST',b'EZ80TS1'));stage=m['labels']['FAIL_STAGE']
pat=bytes([0x32,stage&255,stage>>8])
positions=[i for i in range(len(old)-4) if old[i]==0x3e and old[i+2:i+5]==pat]
assert len(positions)==36,len(positions)
# Keep all old offsets, return targets, buffers and executable ADL bytes intact.
# First instruction really is DI, followed by JP to an appended startup shim.
startup=0x100+len(b);b[:5]=bytes([0xf3,0xc3,startup&255,startup>>8,0])
start_msg=b'EZ80TS1 R15.1 START\r\n$'
# IM1, save caller IX/IY as the original entry did, print, resume at 0105.
start_code=bytes.fromhex('ED 56 DD E5 FD E5')
msg_addr=startup+len(start_code)+len(print_code(0,False))+3
b.extend(start_code+print_code(msg_addr,False)+bytes.fromhex('C3 05 01')+start_msg)
markers=[]
for n,off in enumerate(positions,1):
 here=0x100+len(b);original=old[off:off+5];message=f'TS{n:02d}\r\n$'.encode()
 code=print_code(0,True);msg_addr=here+len(code)+5+3
 b.extend(print_code(msg_addr,True)+original+bytes([0xc3,(0x100+off+5)&255,(0x100+off+5)>>8])+message)
 b[off:off+5]=bytes([0xc3,here&255,here>>8,0,0]);markers.append(dict(marker=f'TS{n:02d}',case=n-1,description=m['cases'][n-1]['description'],original_stage_pc=f'{0x100+off:04X}'))
assert len(b)+0x100<0xf000
m.update(name='EZ80TS1',version='P2 trace R15.1',bytes=len(b),sha256=hash(b),CRC32=f'{zlib.crc32(b)&0xffffffff:08X}',markers=markers,original_COM_SHA256=hash(old),diagnostic_only=True,RTL_change=False)
header=(h/'EZ80TST.vh').read_text();header=re.sub(r"(`define P2_COM_END 16'h)[0-9a-f]+",lambda x:x[1]+f'{0xff+len(b):04x}',header)
dump('EZ80TS1',b,m,header)
# Generate a focused cross-pointer memory diagnostic from the R3 byte emitter.
s=(h/'build_data_r3.py').read_text();a=s.index("label('START');");end=s.index("label('SUBROUTINE');")
body='''label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5)
ref([0xed,0x73],'SAVED_SPS')
ref([0x11],'START_TEXT');ref([0xcd],'PRINT_LOCKED')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
# First phase specifically addresses the reported location via all three pointers.
for index,(writer,reader) in enumerate([('HL','HL'),('HL','IX'),('IX','HL'),('IX','IX'),('IY','HL'),('HL','IY'),('IY','IY')],1):
 stage(str(index));ref([0x11],'TEXT_'+str(index));ref([0xcd],'PRINT_ACTIVE')
 for value in [0xa2,0xa3,0,0xff,0x55,0xaa,0x5a]:
  loadpair(writer,0x020102);emit(0x3e,value);indir(writer,True)
  loadpair(reader,0x020102);indir(reader,False);check(value,0x020102)
# Distinct lane/address patterns, verified through independent registers.
stage('8');ref([0x11],'TEXT_8');ref([0xcd],'PRINT_ACTIVE')
for rep in range(8):
 for off in range(4):
  loadpair('HL',0x020100+off);emit(0x3e,(0xa0+off)^(rep*17));indir('HL',True)
 for pair in ['IX','IY','HL']:
  for off in range(4):
   loadpair(pair,0x020100+off);indir(pair,False);check((0xa0+off)^(rep*17),0x020100+off)
stage('9');ref([0x11],'TEXT_9');ref([0xcd],'PRINT_ACTIVE')
# Reverse direction with indexed stores at lane 0..3 and independent HL reads.
for rep in range(8):
 for off in range(4):
  pair='IX' if off%2==0 else 'IY';loadpair(pair,0x020100+off);emit(0x3e,(0x5f-off)^(rep*17));indir(pair,True)
 for off in range(4):
  loadpair('HL',0x020100+off);indir('HL',False);check((0x5f-off)^(rep*17),0x020100+off)
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
# Printing is only reached in Z80 mode. Preserve caller values and reopen gate.
label('PRINT_ACTIVE');emit(0xf5,0xc5,0xd5,0xe5,0xdd,0xe5,0xfd,0xe5)
gate(0);emit(0xfd,0xe1,0xdd,0xe1,0xe1,0xd1,0xc1,0xf1)
ref([0xcd],'PRINT_LOCKED');emit(0xf5,0xc5);gate(0xa5);gate(0x5a);emit(0xc1,0xf1,0xc9)
label('PRINT_LOCKED');emit(0xf5,0xc5,0xd5,0xe5,0xdd,0xe5,0xfd,0xe5,0xfb,0x0e,9,0xcd,5,0,0xf3,0xed,0x56,0xfd,0xe1,0xdd,0xe1,0xe1,0xd1,0xc1,0xf1,0xc9)
label('START_TEXT');emit(*b'EZ80MX1 R15.1 START\\r\\n$')
for i,t in enumerate(['HL>HL','HL>IX','IX>HL','IX>IX','IY>HL','HL>IY','IY>IY','LANES HL>ALL','LANES IX/IY>HL'],1):
 label('TEXT_'+str(i));emit(*('MX'+str(i)+' '+t+'\\r\\n$').encode())
'''
s=s[:a]+body+s[end:];s=s.replace('EZ80D3','EZ80MX1').replace('R3:','R15.1:')
# Avoid __file__ ambiguity and write all focused test files alongside the originals.
exec(compile(s,str(h/'build_data_r3.py'),'exec'),{'__file__':str((h/'build_data_r3.py').resolve())})
meta=json.loads((h/'EZ80MX1.json').read_text());meta.update(name='EZ80MX1',diagnostic_only=True,RTL_change=False,private_addresses=['020100..020103'],test='HL/IX/IY cross-read and cross-write, all 4 SDRAM byte lanes, 49 basic comparisons plus 128 lane comparisons',CRC32=f'{zlib.crc32((h/"EZ80MX1.COM").read_bytes())&0xffffffff:08X}')
(h/'EZ80MX1.json').write_text(json.dumps(meta,indent=2)+'\n')
print('EZ80TS1',len(b),'bytes',m['CRC32']);print('EZ80MX1',meta['bytes'],'bytes',meta['CRC32'])
