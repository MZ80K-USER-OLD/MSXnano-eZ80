"""Check source scope and excluded page-0 I/O decodes. Not a synthesis estimate."""
from pathlib import Path
import re,json,hashlib
r=Path(__file__).resolve().parent.parent
s=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text();ed=s[s.index('--      ED prefixed instructions'):];a=ed.index('case IRB is');z=ed.index('null; -- NOP, undocumented',a)
nop={int(x,2) for x in re.findall(r'"([01]{8})"',ed[a:z])}
excluded=list(range(0,0x40,8))+list(range(1,0x40,8))+[0x82,0x92,0x8a,0x9a,0x83,0x93,0x8b,0x9b]
assert set(excluded)<=nop
# Extension overrides only use already-supported data/arithmetic classes plus MLT.
# Verify no added IORQ assignment follows the inherited opcode decoder.
overrides=s[s.index('-- R1 only:'):]
assert not re.search(r"IORQ\s*<=\s*'1'",overrides)
# MLT is one nontrivial shared product, with explicit input/result registers.
core=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
assert core.count('Mul_Product<=Mul_Left*Mul_Right')==1
assert 'attribute syn_dspstyle of Mul_Product : signal is "dsp"' in core
assert 'SPL(15 downto 0)<=Mul_Product' in core and 'Upper(to_integer(unsigned(Mul_Target)))<=' not in core
# Confirm original G80A source identity from the restart provenance.
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():
 assert hashlib.sha256((r/'fpga/G80A'/(n+'.vhd')).read_bytes()).hexdigest()==h,n
converted=r/'verification/cpu_1.v'
if converted.exists():
 multipliers=[line for line in converted.read_text().splitlines() if 'assign ' in line and re.search(r'\s\*\s',line)]
 assert len(multipliers)==1,multipliers
result={'excluded_page0_IO_opcode_bytes':[f'ED {v:02X}' for v in excluded],'no_added_IO_assertion':True,'shared_MLT_product_count':1,'DSP_attribute_present':True,'upper_preservation':True,'original_T80_unchanged':True,'physical_DSP_count_verified':False,'converted_multiplier_operators':1 if converted.exists() else None}
(r/'verification_scope_r7.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS R7 scope: page-0 I/O excluded; shared DSP-style MLT; original T80 unchanged')
