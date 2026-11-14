from pathlib import Path
import hashlib
r=Path(__file__).resolve().parent.parent
old=(r/'doc/EZ80MAD_PRE_R13.COM.bin').read_bytes()
assert len(old)==3066 and hashlib.sha256(old).hexdigest()=='22549536a7c53e0348023dbf1717dae92537aa6aa4e4d51506e27f8b815be4bd'
assert old[:5]==bytes.fromhex('DD E5 FD E5 F3')
new=bytes.fromhex('C3 FA 0C 00 00')+old[5:]+bytes.fromhex('F3 ED 56 DD E5 FD E5 C3 05 01')
assert hashlib.sha256(new).hexdigest()=='559dcccbc5f2d38412e730cf6b362ae0aae1713c0e2627936c1334cd1f43c4c7'
assert (r/'hardware_test/EZ80MAD.COM').read_bytes()==new
print('PASS MAD COM startup DI/IM1 shim; original payload addresses unchanged')
