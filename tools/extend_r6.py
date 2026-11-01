"""Apply after extend_r5. Retain the original per-byte T80 block schedule."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal Block_Instruction' not in s
s=s.replace('    signal SPL :', '''    signal Block_Instruction, Block_Long, Instruction_Has_Width : std_logic;
    signal Block_Inc_Result : unsigned(23 downto 0);
    signal SPL :''',1)
s=s.replace('    Extension_State<=', '''    Block_Instruction<='1' when Mode=0 and Extensions_Enabled='1' and ISet="10" and IR(7 downto 5)="101" and
        IR(2 downto 1)="00" and IntCycle='0' and NMICycle='0' else '0';
    Block_Long<=Block_Instruction and Data_Long;
    Block_Inc_Result<=(unsigned(Upper(to_integer(unsigned(RegAddrA)))) & unsigned(RegBusA))-1 when IncDec_16(3)='1'
        else (unsigned(Upper(to_integer(unsigned(RegAddrA)))) & unsigned(RegBusA))+1;
    Extension_State<=''',1)
s=s.replace("            Arith_Left<=", "            Instruction_Has_Width<='0';\n            Arith_Left<=",1)
s=s.replace("                            Data_Long<='0';Stream_Long<='0';", "                            Data_Long<='0';Stream_Long<='0';Instruction_Has_Width<='0';",1)
s=s.replace("                            Data_Long<=Width_Pending and Width_Code(3);", "                            Instruction_Has_Width<=Width_Pending;\n                            Data_Long<=Width_Pending and Width_Code(3);",1)
s=s.replace("else Width_Pending<='0';Data_Long<='0';Stream_Long<='0';end if;", "else Width_Pending<='0';Data_Long<='0';Stream_Long<='0';Instruction_Has_Width<='0';end if;",1)
s=s.replace('                        PC <= PC - 2;', '''                        -- Refetch the width prefix as well as ED and the block opcode.
                        -- This also gives an interrupt a restart PC including the suffix.
                        if Block_Instruction='1' and Instruction_Has_Width='1' then PC<=PC-3;
                        else PC <= PC - 2;end if;''',1)
s=s.replace("            if Wide_IncDec='1'", '''            -- Use exactly the original lower16 register write edge: once per byte,
            -- never while T2 is held by WAIT. BC decrements in M1/T3; HL/DE in data T2.
            if Block_Long='1' and IncDec_16(2)='1' and
               ((MCycle="001" and TState=3) or (MCycle/="001" and TState=2 and Wait_n='1')) then
                Upper(to_integer(unsigned(RegAddrA)))<=std_logic_vector(Block_Inc_Result(23 downto 16));
            end if;
            if Wide_IncDec='1' ''',1)
s=s.replace('                    if ID16 = 0 then', '''                    if Block_Long='1' then
                        if Block_Inc_Result=0 then IncDecZ<='0';else IncDecZ<='1';end if;
                    elsif ID16 = 0 then''',1)
p.write_text(s)

# The inherited I/O qualifier suppressed interrupt-acknowledge IORQ as well.
p=r/'fpga/G80A_eZ80/g80a_ez80.vhd';s=p.read_text()
old="IReq_Inhibit <= not IORQ;"
assert s.count(old)==1
s=s.replace(old,"-- Preserve I/O qualification, but allow the interrupt acknowledge cycle.\n                IReq_Inhibit <= not (IORQ or not IntCycle_n);")
p.write_text(s)
