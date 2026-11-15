from pathlib import Path
r=Path(__file__).resolve().parent
s=(r/'build_sleep_r20_2.py').read_text()
s=s.replace("r=Path(__file__).resolve().parent",'r=Path('+repr(str(r))+')')
s=s.replace("plans=[dict(src=src,madl=madl,pref=pref)for src in(0,1)for madl in(0,1)for pref in(None,)]", "plans=[dict(src=0,madl=0,pref=None)]")
s=s.replace('code +=[0xed,0x76,0xf3,','code +=[0x00,0x00,0xf3,')
s=s.replace('readcheck(0x0a8103,0xa7)','readcheck(0x0a8103,0x53)')
s=s.replace("writebytes(native,after);emit(0x31","writebytes(native,after);\n for address,value in sorted(native.items()):\n  if address not in(0x0a7009,0x0a700a):readcheck(address,value)\n emit(0x31")
s=s.replace('EZ80SL2','EZ80SP0').replace('R20.2','R20.3 PRE-SLP')
s=s.replace('expected_sleep_entries=4','expected_sleep_entries=0')
s=s.replace("production_wake='RESET only'", "production_wake='SLP NOT EXECUTED'")
exec(compile(s,str(r/'build_sleep_r20_2.py'),'exec'),{'__file__':str(r/'build_sleep_r20_2.py')})
