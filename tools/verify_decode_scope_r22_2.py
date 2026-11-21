from pathlib import Path
import re
r=Path(__file__).resolve().parent.parent;s=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text()
a=s.index('--      ED prefixed instructions');b=s.index('                if not Indexed_Pair_Active',a)
assert s.count('if Block_IO_Repeat then')==1
row=s.index('when "10010100"|"10011100"|"10110100"|"10111100"|',a);body=s.index('if Block_IO_Repeat then',row)
assert a<row<body<b
assert s.index('                        end case;',body)<b
nop=s[s.index('case IRB is',a):s.index('null; -- NOP, undocumented',a)]
for op in [0x94,0x9c,0xb4,0xbc,0xc2,0xca,0xc3,0xcb]:assert '"'+format(op,'08b')+'"'not in nop
print('PASS repeat decode restricted to dedicated ED row; no global repeat override')
