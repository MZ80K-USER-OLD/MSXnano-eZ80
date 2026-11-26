"""Append-only COM probes: original test body/labels stay at their original addresses.
Print before unlock only; use existing locked cleanup/DOS result path afterwards.
"""
from pathlib import Path
import json,hashlib,zlib
r=Path(__file__).resolve().parent
specs=[('EZ80MX0','EZ80MIX',0x1f5,'SETUP ONLY'),('EZ80MX1','EZ80MIX',0x3b7,'FIRST MIXED CALL + CHECKS'),('EZ80MX2','EZ80MIX',None,'FULL MIX'),('EZ80MA1','EZ80MAD',None,'FULL MAD')]
rows=[]
for name,src,stop,desc in specs:
 data=bytearray((r/(src+'.COM')).read_bytes());orig=bytes(data);m=json.loads((r/(src+'.json')).read_text());labels=m['labels'].copy()
 assert data[:5]==(bytes.fromhex('DD E5 FD E5 F3') if src=='EZ80MIX' else bytes.fromhex('C3 FA 0C 00 00'))
 def add(bs):
  at=0x100+len(data);data.extend(bs);return at
 def word(n):return n.to_bytes(2,'little')
 startmsg=add((name+' R29.1: START '+desc+'\r\n$').encode('ascii'))
 passmsg=add((name+' R29.1: PASS\r\n$').encode('ascii'))
 # Preserve caller values and perform the print before any extension unlock.
 # DOS/BIOS can EI internally. DI is explicit after the call and in replayed entry.
 boot=add(bytes.fromhex('F3 F5 C5 D5 E5 DD E5 FD E5')+b'\x11'+word(startmsg)+bytes.fromhex('FB 0E 09 CD 05 00 F3 FD E1 DD E1 E1 D1 C1 F1')+orig[:5]+b'\xc3'+word(0x105))
 data[:5]=b'\xc3'+word(boot)+b'\0\0'
 needle=b'\x11'+word(labels['MSG_PASS']);assert bytes(data).count(needle)==1
 at=bytes(data).index(needle);data[at+1:at+3]=word(passmsg)
 if stop is not None:
  assert stop in (0x1f5,0x3b7)
  exitat=add(b'\x3e\x01\x32'+word(labels['STATUS'])+b'\x11'+word(passmsg)+b'\xc3'+word(labels['FINISH']))
  data[stop-0x100:stop-0x100+3]=b'\xc3'+word(exitat)
 labels.update(PROBE_BOOT=boot,PROBE_START_MESSAGE=startmsg,PROBE_PASS_MESSAGE=passmsg)
 if stop is not None:labels['PROBE_STOP']=stop;labels['PROBE_EXIT']=exitat
 obj=dict(name=name,source=src,source_sha256=hashlib.sha256(orig).hexdigest(),description=desc,labels=labels,origin=256,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),crc32=f'{zlib.crc32(data):08X}',payload_addresses_preserved=True,added_BDOS_before_unlock_only=True,DI_after_BDOS=True)
 for dest in [r,r.parent]: (dest/(name+'.COM')).write_bytes(data)
 (r/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 (r/(name+'.hex')).write_text(''.join(f'{x:02x}\n'for x in data))
 (r/(name+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in labels.items())+f"`define P2_COM_END 16'h{255+len(data):04x}\n")
 lines=['; R29.1 diagnostic; byte-for-byte resolved source.','; '+desc,'; EI; BDOS 9; DI occurs before extension unlock.','ORG 0100h']
 for i in range(0,len(data),16):lines.append('    DEFB '+','.join(f'0{x:02X}h'for x in data[i:i+16])+f' ; {i+256:04X}')
 (r/(name+'.asm')).write_text('\n'.join(lines)+'\n');rows.append(obj)
 print(name,'bytes',len(data),'CRC32',obj['crc32'])
(r.parent/'doc/R29_1_DIAGNOSTIC_COM_MANIFEST.json').write_text(json.dumps(rows,indent=2)+'\n')
