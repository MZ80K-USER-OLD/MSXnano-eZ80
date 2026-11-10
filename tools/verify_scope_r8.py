from pathlib import Path
import re,json,hashlib
r=Path(__file__).resolve().parent.parent
core=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text();mcode=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text()
ea=core[core.index("    EA_Active<="):core.index("    PEA_Active<=")]
expected={2,3,0x12,0x13,0x22,0x23,0x32,0x33,0x54,0x55,0x65,0x66}
if "Opcode_Class(10)='1'" in ea:
 a=core.index('if op=x"02"');z=core.index('then c(10)',a)
 assert {int(n,16) for n in re.findall(r'op=x"([0-9A-F]{2})"',core[a:z])}==expected
 assert 'ISet="10"' in ea and "Extensions_Enabled='1'" in ea
else:
 assert {int(n,16) for n in re.findall(r'IR=x"([0-9A-F]{2})"',ea)}==expected
assert core.count('EA_Result<=std_logic_vector(Indexed_Address)')==1
assert core.count('Indexed_Address<=')==1
if 'Upper_Port_Events' in core:
 assert "Upper_Port_Events(1)<=LEA_Commit and Data_Long;" in core
 assert 'Upper_Mask(EA_Target,Upper_Port_Events(1))' in core
 assert 'Upper_Mask(EA_Result(23 downto 16),Upper_Port_Events(1))' in core
 assert "if Upper_Port_WE='1' then Upper(to_integer(unsigned(Upper_Port_Index)))<=Upper_Port_Data;" in core
else:
 assert "if LEA_Commit='1' and Data_Long='1' then Upper" in core
new=mcode[mcode.index('-- LEA/PEA consume'):]
for s in ["I_RETN<='0'",'IMode<="11"',"Jump<='0'","Save_ALU<='0'","Read_To_Acc<='0'"]:assert s in new,s
assert not re.search(r"IORQ\s*<=\s*'1'",mcode[mcode.index('-- R1 only:'):])
ed=mcode[mcode.index('--      ED prefixed instructions'):];a=ed.index('case IRB is');z=ed.index('null; -- NOP, undocumented',a)
nop={int(x,2) for x in re.findall(r'"([01]{8})"',ed[a:z])}
excluded=set(range(0,0x40,8))|set(range(1,0x40,8))|{0x82,0x92,0x8a,0x9a,0x83,0x93,0x8b,0x9b};excluded.discard(0x31);assert excluded<=nop # ED31 = LD IY,(HL), not OUT0
for n,h in json.loads((r/'doc/provenance.json').read_text()).items():assert hashlib.sha256((r/'fpga/G80A'/(n+'.vhd')).read_bytes()).hexdigest()==h
result=dict(EA_opcodes=[f'ED {v:02X}' for v in sorted(expected)],existing_indexed_adder_reused=True,source_read_port_reused=True,short_LEA_upper_preserved=True,RETN_IM_NEG_aliases_suppressed_only_while_enabled=True,no_new_IO=True,original_T80_unchanged=True,GOWIN_area_verified=False)
(r/'verification_scope_r8.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS R8 scope: shared indexed adder, 12 EA opcodes, no new I/O')
