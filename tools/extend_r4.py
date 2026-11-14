"""Apply after rebuild_from_t80.py, extend_r2.py and extend_r3.py."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal EX_SP_Long' not in s
s=s.replace('    signal SPL :', '''    signal Byte_Absolute, EX_SP_Long, EX_SP_Result_WE : std_logic;
    signal EX_SP_Index : std_logic_vector(2 downto 0);
    signal EX_SP_Read : std_logic_vector(23 downto 0);
    signal EX_SP_Address : unsigned(23 downto 0);
    signal SPL :''',1)
s=s.replace('    Extension_State<=', '''    Byte_Absolute<='1' when Extensions_Enabled='1' and (Data_Long='1' or Stream_Long='1') and ISet="00" and
        (IR=x"32" or IR=x"3A") and IntCycle='0' and NMICycle='0' else '0';
    EX_SP_Long<='1' when Extensions_Enabled='1' and Data_Long='1' and ISet="00" and IR=x"E3" and IntCycle='0' and NMICycle='0' else '0';
    EX_SP_Index<=XY_State(1) & "11" when XY_State/="00" else Alternate & "10";
    EX_SP_Result_WE<='1' when EX_SP_Long='1' and MCycle="111" and TState=3 else '0';
    process(SPL,MCycle) variable offset:natural range 0 to 2;
    begin
        offset:=0;
        if MCycle="010" or MCycle="101" then offset:=1;
        elsif MCycle="011" or MCycle="110" then offset:=2;end if;
        EX_SP_Address<=SPL+offset;
    end process;
    Extension_State<=''',1)
s=s.replace('            Upper <=', '            EX_SP_Read<=(others=>\'0\');\n            Upper <=',1)
s=s.replace("if Pair_Absolute='1' and Set_Addr_To=aZI then", "if EX_SP_Long='1' and Set_Addr_To=aSP then A_BANK<=std_logic_vector(EX_SP_Address(23 downto 16));\n                    elsif (Pair_Absolute='1' or Byte_Absolute='1') and Set_Addr_To=aZI then",1)
s=s.replace("if Wide_Stack='1' then A<=", "if EX_SP_Long='1' then A<=std_logic_vector(EX_SP_Address(15 downto 0));elsif Wide_Stack='1' then A<=",1)
s=s.replace("elsif Pair_Absolute='1' and Stream_Long='1' then A<=TmpAddr;", "elsif (Pair_Absolute='1' or Byte_Absolute='1') and Stream_Long='1' then A<=TmpAddr;",1)
# Keep cycles 6/7 out of legacy indexed fetch/return paths during EX(SPL).
s=s.replace("and Pair_Absolute='0' then", "and Pair_Absolute='0' and EX_SP_Long='0' then")
s=s.replace("and Pair_Absolute='0') or", "and Pair_Absolute='0' and EX_SP_Long='0') or")
s=s.replace("and Pair_Absolute='0') then", "and Pair_Absolute='0' and EX_SP_Long='0') then")
s=s.replace("            if Wide_IncDec='1'", '''            if EX_SP_Long='1' and TState=3 then
                case MCycle is
                when "010"=>EX_SP_Read(7 downto 0)<=DI_Reg;
                when "011"=>EX_SP_Read(15 downto 8)<=DI_Reg;
                when "100"=>EX_SP_Read(23 downto 16)<=DI_Reg;
                when others=>null;
                end case;
            end if;
            if EX_SP_Result_WE='1' then Upper(to_integer(unsigned(EX_SP_Index)))<=EX_SP_Read(23 downto 16);end if;
            if Wide_IncDec='1' ''',1)
s=s.replace('    RegAddrA <=', "    RegAddrA <= EX_SP_Index when EX_SP_Long='1' else",1)
s=s.replace('ExchangeDH, IncDec_16, MCycle, TState, Wait_n)', 'ExchangeDH, IncDec_16, MCycle, TState, Wait_n, EX_SP_Result_WE)')
s=s.replace("        RegWEH <= '0';", "        RegWEH <= EX_SP_Result_WE;",1).replace("        RegWEL <= '0';", "        RegWEL <= EX_SP_Result_WE;",1)
# RegDIH/DIL have a distinct combinational process; add read buffer to sensitivity.
s=s.replace('process (Save_Mux, RegBusB, RegBusA_r, ID16,\n            ExchangeDH, IncDec_16, MCycle, TState, Wait_n, EX_SP_Result_WE)',
 '''process (Save_Mux, RegBusB, RegBusA_r, ID16,
            ExchangeDH, IncDec_16, MCycle, TState, Wait_n, EX_SP_Result_WE, EX_SP_Read)''')
s=s.replace('        RegDIH <= Save_Mux;\n        RegDIL <= Save_Mux;', '''        if EX_SP_Result_WE='1' then RegDIH<=EX_SP_Read(15 downto 8);RegDIL<=EX_SP_Read(7 downto 0);
        else RegDIH <= Save_Mux;RegDIL <= Save_Mux;end if;''',1)
s=s.replace("                if Pair_Absolute='1' then\n                    if Pair_SP=", "                if EX_SP_Long='1' then BusB<=Upper(to_integer(unsigned(EX_SP_Index)));\n                elsif Pair_Absolute='1' then\n                    if Pair_SP=",1)
p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();a=s.rindex('        end process;')
s=s[:a]+'''
                -- R4 absolute byte access: immediate width independent from data block.
                if Ext_Active='1' and (Data_Long='1' or Stream_Long='1') and Mode=0 and ISet="00" and IntCycle='0' and NMICycle='0' and (IR=x"32" or IR=x"3A") then
                    if Stream_Long='1' then lastaddr:=4;else lastaddr:=3;end if;
                    cycle:=to_integer(unsigned(MCycle));MCycles<=std_logic_vector(to_unsigned(lastaddr+1,3));
                    Inc_PC<='0';LDZ<='0';LDW<='0';Write<='0';Read_To_Acc<='0';Read_To_Reg<='0';
                    Set_Addr_To<=aNone;Inc_WZ<='0';IncDec_16<="0000";NoRead<='0';
                    if cycle=1 then TStates<="100";else TStates<="011";end if;
                    if cycle=2 then Inc_PC<='1';LDZ<='1';end if;
                    if cycle=3 then Inc_PC<='1';LDW<='1';end if;
                    if cycle=4 and lastaddr=4 then Inc_PC<='1';end if;
                    if cycle=lastaddr then Set_Addr_To<=aZI;Set_BusB_To<="0111";
                    elsif cycle=lastaddr+1 then
                        if IR=x"32" then Write<='1';else Read_To_Acc<='1';end if;
                    end if;
                end if;
                -- R4 EX(SPL),HL/IX/IY. Read all 3 bytes, then write all 3 bytes.
                -- SPL is never changed. The register commits after the final write.
                if Ext_Active='1' and Data_Long='1' and Mode=0 and ISet="00" and IntCycle='0' and NMICycle='0' and IR=x"E3" then
                    MCycles<="111";Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";
                    Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';Set_Addr_To<=aSP;NoRead<='0';
                    ExchangeDH<='0';ExchangeRp<='0';
                    if MCycle="001" then TStates<="100";else TStates<="011";end if;
                    case MCycle is
                    when "100"=>Set_BusB_To<="0101";
                    when "101"=>Write<='1';Set_BusB_To<="0100";
                    when "110"=>Write<='1';Set_BusB_To<="1110";
                    when "111"=>Write<='1';Set_Addr_To<=aNone;
                    when others=>null;
                    end case;
                end if;
''' +s[a:];p.write_text(s)
