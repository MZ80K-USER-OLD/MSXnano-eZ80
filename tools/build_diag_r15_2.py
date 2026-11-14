"""Software-only R15.2: code-readback control test and indexed bank-boundary test."""
from pathlib import Path
import json,re,hashlib,zlib,ast
root=Path(__file__).resolve().parent.parent;h=root/'hardware_test'
# Reuse the audited lock/DOS/DI/IM1, register-preserving printer and file writer.
prev=(root/'tools/build_diag_r15_1.py').read_text();g={'__file__':__file__}
exec(compile(prev[:prev.index('# Trace the unchanged')],str(root/'tools/build_diag_r15_1.py'),'exec'),g)
printer=g['print_code'];dump=g['dump']
old=(h/'EZ80CTL.COM').read_bytes();meta=json.loads((h/'EZ80CTL.json').read_text());labels=meta['labels'];assert len(old)==23296
b=bytearray(old.replace(b'EZ80CTL',b'EZ80CT1'))
def append_marker(message,continuation,original=b'',restore=True,initial=False):
 a=0x100+len(b);head=bytes.fromhex('ED 56 DD E5 FD E5') if initial else b''
 msgaddr=a+len(head)+len(printer(0,restore))+len(original)+3
 b.extend(head+printer(msgaddr,restore)+original+bytes([0xc3,continuation&255,continuation>>8])+message.encode()+b'$')
 return a
def patch5(address,destination):b[address-0x100:address-0x100+5]=bytes([0xc3,destination&255,destination>>8,0,0])
startup=append_marker('EZ80CT1 R15.2 START\r\n',0x105,restore=False,initial=True)
b[:5]=bytes([0xf3,0xc3,startup&255,startup>>8,0])
load=labels['STAGE_C'];a=append_marker('CT1 LOAD\r\n',load+5,old[load-0x100:load-0x100+5]);patch5(load,a)
ret=labels['RETURN'];assert old[ret-0x100-5:ret-0x100]==bytes([0x5b,0xc3,0,0,9])
a=append_marker('CT4 CHECK\r\n',ret+5,old[ret-0x100:ret-0x100+5]);patch5(ret,a)
# Appended verifier: expected bytes are the original loader's immediate literals.
# Every original instruction/operand/target remains at its original address.
verify=0x100+len(b);code=bytearray();local={};fix=[]
def e(*xs):code.extend(xs)
def label(n):local[n]=verify+len(code)
def ref(op,n):e(op,0,0);fix.append((len(code)-2,n))
def absop(op,addr):e(op,addr&255,addr>>8)
# Message addresses are fixed after emitting the verifier.
msg2=0 # placeholder, corrected below
startpr=len(code);code.extend(printer(0,True))
e(0x5b,0x21,0,0,9);absop(0x11,load+11);absop(1,meta['payload_bytes'])
label('LOOP');e(0x5b,0x7e);absop(0x32,labels['DIAG_ACT']);e(0x1a);absop(0x32,labels['DIAG_EXP'])
e(0xe5);absop(0x21,labels['DIAG_ACT']);e(0xbe,0xe1);ref(0xc2,'BAD')
e(0x5b,0x23,*([0x13]*9),0x0b,0x78,0xb1);ref(0xc2,'LOOP')
runpr=len(code);code.extend(printer(0,True));e(0x5b,0xc3,0,0,9)
label('BAD');e(0x3e,ord('V'));absop(0x32,labels['FAIL_STAGE']);e(0x3e,1);absop(0x32,labels['DIAG_MEM'])
e(0x7d);absop(0x32,labels['DIAG_ADDR0']);e(0x7c);absop(0x32,labels['DIAG_ADDR1']);e(0x3e,9);absop(0x32,labels['DIAG_ADDR2']);absop(0xc3,labels['FAIL'])
label('MSG2');code.extend(b'CT2 VERIFY\r\n$');label('MSG3');code.extend(b'CT3 RUN\r\n$')
code[startpr:startpr+len(printer(0,True))]=printer(local['MSG2'],True)
code[runpr:runpr+len(printer(0,True))]=printer(local['MSG3'],True)
for off,n in fix:code[off:off+2]=local[n].to_bytes(2,'little')
b.extend(code);patch5(ret-5,verify)
# Prove that all payload bytes still have the old expected values and addresses.
for i in range(meta['payload_bytes']):
 off=load+11+9*i-0x100;assert old[off]==b[off]
assert len(b)+0x100<0xf000
newmeta=dict(meta);newmeta.update(name='EZ80CT1',release='R15.2 diagnostic',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),CRC32=f'{zlib.crc32(b)&0xffffffff:08X}',original_SHA256=hashlib.sha256(old).hexdigest(),verify_entry=verify,verify_labels=local,verify_before_ADL_execution=True,FPGA_unchanged=True)
header=(h/'EZ80CTL.vh').read_text();header=re.sub(r"(`define CTL_COM_END 16'h)[0-9a-f]+",lambda m:m[1]+f'{0xff+len(b):04x}',header)
dump('EZ80CT1',b,newmeta,header)
# Focused indexed-carry test, independent write/read register pairs.
src=(h/'build_data_r3.py').read_text();env={'__file__':str((h/'build_data_r3.py').resolve())};exec(src[:src.index("label('START');")],env)
# Reuse only the R15.1 audited Z80 progress-printer helpers, not its test body.
tree=ast.parse(prev);body=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
pr=body[body.index('# Printing is only reached'):body.index("label('START_TEXT')")]
body2='''label('START');emit(0xf3,0xed,0x56,0xdd,0xe5,0xfd,0xe5)
ref([0xed,0x73],'SAVED_SPS');ref([0x11],'START_TEXT');ref([0xcd],'PRINT_LOCKED')
gate(0xa5);gate(0x5a);emit(0xed,0x78,0xfe,0xe1);ref([0xc2],'UNSUPPORTED')
cases=[('HL',0x030000,0,'HL',0x030000,0),('IX',0x02ffff,1,'HL',0x030000,0),('HL',0x030000,0,'IX',0x02ffff,1),('IY',0x030000,-1,'HL',0x02ffff,0),('HL',0x02ffff,0,'IY',0x030000,-1),('IX',0x03ffff,1,'HL',0x040000,0),('HL',0x040000,0,'IX',0x03ffff,1),('IX',0x01ffff,1,'HL',0x020000,0),('HL',0x020000,0,'IX',0x01ffff,1)]
for index,(wp,wa,wd,rp,ra,rd) in enumerate(cases,1):
 stage(str(index));ref([0x11],'TEXT_'+str(index));ref([0xcd],'PRINT_ACTIVE')
 address=(wa+wd)&0xffffff
 for value in [0x96,0x97,0,0xff,0x55,0xaa,0xfe,1,0x7f,0x80]:
  for off,sentinel in [(-1,0x39),(0,0x5a),(1,0xc6)]:
   loadpair('HL',(address+off)&0xffffff);emit(0x3e,sentinel);indir('HL',True)
  loadpair(wp,wa);emit(0x3e,value);indir(wp,True,wd)
  loadpair(rp,ra);indir(rp,False,rd);check(value,address)
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
'''+pr+'''label('START_TEXT');emit(*b'EZ80BN1 R15.2 START\\r\\n$')
texts=['HL>HL 030000','IX+1>HL 030000','HL>IX+1 030000','IY-1>HL 02FFFF','HL>IY-1 02FFFF','IX+1>HL 040000','HL>IX+1 040000','IX+1>HL 020000','HL>IX+1 020000']
for i,t in enumerate(texts,1):label('TEXT_'+str(i));emit(*('BN'+str(i)+' '+t+'\\r\\n$').encode())
'''
footer=src[src.index("label('SUBROUTINE');"):].replace('EZ80D3','EZ80BN1').replace('R3:','R15.2:')
exec(body2+footer,env)
meta=json.loads((h/'EZ80BN1.json').read_text());meta.update(name='EZ80BN1',release='R15.2 diagnostic',FPGA_unchanged=True,private_addresses=['01FFFF..040001'],checks=90,phase_descriptions=['HL>HL 030000','IX+1>HL 030000','HL>IX+1 030000','IY-1>HL 02FFFF','HL>IY-1 02FFFF','IX+1>HL 040000','HL>IX+1 040000','IX+1>HL 020000','HL>IX+1 020000'],CRC32=f'{zlib.crc32((h/"EZ80BN1.COM").read_bytes())&0xffffffff:08X}')
(h/'EZ80BN1.json').write_text(json.dumps(meta,indent=2)+'\n')
for n in ['EZ80CT1','EZ80BN1']:
 m=json.loads((h/f'{n}.json').read_text());print(n,m['bytes'],m['CRC32'])
