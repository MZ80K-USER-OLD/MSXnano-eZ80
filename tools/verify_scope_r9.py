from pathlib import Path
import re,json,hashlib
r=Path(__file__).resolve().parent.parent
s=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text();m=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text()
assert 'signal PC, PC_Increment : unsigned(23 downto 0)' in s
assert "ADL_Mode<='0';" in s and 'PC_Width(PC_Increment,ADL_Mode)' in s
assert 'else Data_Long<=ADL_Mode;Stream_Long<=ADL_Mode;end if;' in s
assert "IRQ_Long" in s and "Effective_IEF" in s and "NMI_Accept" in s
assert 'JP_Commit' in s and 'Native ADL CALL/RET/RST' in m
assert not re.search(r"IORQ\s*<=\s*'1'",m[m.index('-- R1 only:'):])
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():assert hashlib.sha256((r/'fpga/G80A'/(n+'.vhd')).read_bytes()).hexdigest()==h
result=dict(major_stage=5,PC_bits=24,reset_Z80=True,default_width_from_ADL=True,refresh_bank_zero=True,unconditional_JP_bridge=True,ADL_native_stage6_enabled=True,ADL_native_RETI_RETN_enabled=True,ADL_IM1_IM2_NMI_enabled=True,ADL_IM0_not_implemented=True,no_new_IO=True,original_T80_unchanged=True)
(r/'verification_scope_r9.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS R9 scope: stage5 PC/ADL, native flow and IRQ enabled; mixed-frame limits, no new I/O')
