"""Small CASE0 diagnostics for the unchanged R22 bitstream."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent
base=(r/'build_ior_r22.py').read_text()
for suffix,count,execute in [('0',3,False),('1',1,True),('3',3,True)]:
 name='EZ80IR'+suffix;s=base.replace('EZ80IOR',name).replace('R22','R22.1')
 # Retain the same entry, suffix, counter-upper byte and memory-bank context as CASE0.
 s=s.replace('for src in(0,1):','for src in(0,):').replace('for op in(0x94,0x9c,0xb4,0xbc,0xc2,0xca,0xc3,0xcb):','for op in(0x94,):').replace('for force in(0,1):','for force in(0,):').replace('count=3;bc=3 if wide else 0x7a0003;',f'count={count};bc=count if wide else 0x7a0000|count;')
 # Progress printing must return to the MSX context before DOS, then DI immediately after DOS.
 s=s.replace("gate(0xd8);cases=[];progress_labels=[]", '''gate(0xd8);cases=[];progress_labels=[];checkpoint_labels=[]
def checkpoint(n):
 gate(0xd0);gate(0);ref([0x11],n);emit(0xfb,0x0e,9,0xcd,5,0,0xf3);gate(0xa5);gate(0x5a);gate(0xd8);checkpoint_labels.append(n)
''')
 # Verify memory initialization, avoiding a loader failure being mistaken for repeat failure.
 s=s.replace("   start=0x0a8000", "   for t in targets:readcheck(t,value^255)\n   checkpoint('RAM_OK')\n   start=0x0a8000")
 if not execute:
  # Execute a same-length pair of NOPs instead of the new instruction; all setup and returns remain.
  s=s.replace('code +=[0xed,op,', 'code +=[0,0,')
 # Read back every executable byte using the known independent memory-read path.
 s=s.replace("   emit(0x5b,0xc3,0,0x60,0x0a);label(after)", '''   for a,v in sorted(native.items()):
    expected=(after,0) if a==0x0a7009 else (after,1) if a==0x0a700a else v
    # Resolve symbolic low/high return bytes via bytefix at the literal comparison.
    loadpair('HL',a);indir('HL',False)
    if isinstance(expected,tuple):
     sa('DIAG_ACT');emit(0xfe,0);bytefix.append((len(b)-1,after,0,expected[1]));ok='READ_CODE_OK_'+str(a);ref([0xca],ok)
     emit(0x3e,0);bytefix.append((len(b)-1,after,0,expected[1]));sa('DIAG_EXP');address_context(a);ref([0xc3],'FAIL');label(ok)
    else:check(v,a)
   checkpoint('CODE_OK')
   checkpoint('ENTER_TEST')
   emit(0x5b,0xc3,0,0x60,0x0a);label(after)
   checkpoint('RETURN_OK')''')
 if not execute:
  s=s.replace('hl+(-count if op&8 else count)','hl+0')
  s=s.replace('nextde=de if op&0x40 else (de+(-count if op&8 else count))&0xffffff','nextde=de')
  s=s.replace('expected=[0,0,0 if wide else 0x7a,',"expected=[*bc.to_bytes(3,'little'),")
  s=s.replace('(f0&0xbd)|0x40|(2 if value&128 else 0)','f0')
  s=s.replace('for t in targets:readcheck(t,value)','for t in targets:readcheck(t,value^255)')
 s=s.replace('\nfor at,name,off,i in bytefix:', "\nfor n in checkpoint_labels:\n label(n);emit(*(n+'\\r\\n$').encode())\nfor at,name,off,i in bytefix:")
 # Store readable configuration alongside generated assembly and binary.
 scope={'version':'R22.1 tests only','bitstream':'unchanged R22','count':count,'execute_INI2R':execute,'TPA_max_end_exclusive':'<4000h','readback_executable_bytes':True}
 s=s.replace("physical_external_IO_device_tested=False)","physical_external_IO_device_tested=False,diagnostic_config="+repr(scope)+")")
 ns={'__file__':str(r/('generated_'+suffix+'.py'))};exec(compile(s,'generated_'+suffix,'exec'),ns)
 assert len(ns['b'])+0x100<0x4000,(name,len(ns['b']))
