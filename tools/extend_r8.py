"""R8 LEA/PEA: reuse the existing indexed address adder; latch before writes."""
from pathlib import Path
import re
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal EA_Active' not in s
s=s.replace('    signal SPL :', '''    signal EA_Active, PEA_Active, PEA_Long, LEA_Commit : std_logic;
    signal EA_Source, EA_Target, RegAddrC_Base : std_logic_vector(2 downto 0);
    signal EA_Result : std_logic_vector(23 downto 0);
    signal SPL :''',1)
s=s.replace('    Extension_State<=', '''    EA_Active<='1' when Mode=0 and Extensions_Enabled='1' and ISet="10" and IntCycle='0' and NMICycle='0' and
        (IR=x"02" or IR=x"03" or IR=x"12" or IR=x"13" or IR=x"22" or IR=x"23" or
         IR=x"32" or IR=x"33" or IR=x"54" or IR=x"55" or IR=x"65" or IR=x"66") else '0';
    PEA_Active<=EA_Active when IR=x"65" or IR=x"66" else '0';
    PEA_Long<=PEA_Active and Data_Long;
    EA_Source<="111" when IR=x"03" or IR=x"13" or IR=x"23" or IR=x"33" or IR=x"54" or IR=x"66" else "011";
    EA_Target<="011" when IR=x"32" or IR=x"54" else "111" when IR=x"33" or IR=x"55" else Alternate & IR(5 downto 4);
    LEA_Commit<='1' when EA_Active='1' and PEA_Active='0' and MCycle="010" and TState=5 else '0';
    RegAddrC<=EA_Source when EA_Active='1' else RegAddrC_Base;
    Extension_State<=''',1)
# Only replace the three original registered assignments, not the override above.
s=re.sub(r'RegAddrC <=', 'RegAddrC_Base <=',s)
s=s.replace("            Instruction_Has_Width<=", "            EA_Result<=(others=>'0');\n            Instruction_Has_Width<=",1)
s=s.replace("                    if EX_SP_Long='1' and Set_Addr_To=aSP", "                    if EX_SP_Long='1' and Set_Addr_To=aSP",1)
s=s.replace("Set_Addr_To=aSP and Wide_Stack='1'", "Set_Addr_To=aSP and (Wide_Stack='1' or PEA_Long='1')",1)
s=s.replace("elsif Wide_Stack='1' then A<=", "elsif Wide_Stack='1' or PEA_Long='1' then A<=",1)
s=s.replace("if Wide_Stack='1' or Wide_IncDec='1' then", "if Wide_Stack='1' or Wide_IncDec='1' or PEA_Long='1' then",1)
s=s.replace("            if Mul_Active='1' and MCycle=", '''            -- The displacement is stable after the external read's falling T3 edge.
            -- Share Indexed_Address, then hold all 24 bits through destination/stack writes.
            if EA_Active='1' and MCycle="010" and TState=3 then EA_Result<=std_logic_vector(Indexed_Address);end if;
            if LEA_Commit='1' and Data_Long='1' then Upper(to_integer(unsigned(EA_Target)))<=EA_Result(23 downto 16);end if;
            if Mul_Active='1' and MCycle=''',1)
s=s.replace("                if I_RLD = '1' then", '''                if PEA_Active='1' then
                    if Data_Long='1' then
                        case MCycle is
                        when "011"=>DO<=EA_Result(23 downto 16);
                        when "100"=>DO<=EA_Result(15 downto 8);
                        when "101"=>DO<=EA_Result(7 downto 0);
                        when others=>null;
                        end case;
                    else
                        if MCycle="011" then DO<=EA_Result(15 downto 8);elsif MCycle="100" then DO<=EA_Result(7 downto 0);end if;
                    end if;
                end if;
                if I_RLD = '1' then''',1)
s=s.replace('    RegAddrA <= Mul_Target',"    RegAddrA <= EA_Target when LEA_Commit='1' else Mul_Target",1)
s=s.replace('Arith_Commit, Mul_Reg_Commit)', 'Arith_Commit, Mul_Reg_Commit, LEA_Commit)')
s=s.replace('Mul_Reg_Commit, Mul_Product)', 'Mul_Reg_Commit, Mul_Product, LEA_Commit, EA_Result)')
s=s.replace('EX_SP_Result_WE or Arith_Commit or Mul_Reg_Commit;', 'EX_SP_Result_WE or Arith_Commit or Mul_Reg_Commit or LEA_Commit;')
s=s.replace("        if Mul_Reg_Commit='1' then RegDIH", "        if LEA_Commit='1' then RegDIH<=EA_Result(15 downto 8);RegDIL<=EA_Result(7 downto 0);\n        elsif Mul_Reg_Commit='1' then RegDIH",1)
p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();pos=s.rindex('        end process;')
s=s[:pos]+'''
                -- LEA/PEA consume one displacement byte, regardless of Stream_Long.
                if Ext_Active='1' and Mode=0 and ISet="10" and IntCycle='0' and NMICycle='0' and
                    (IR=x"02" or IR=x"03" or IR=x"12" or IR=x"13" or IR=x"22" or IR=x"23" or
                     IR=x"32" or IR=x"33" or IR=x"54" or IR=x"55" or IR=x"65" or IR=x"66") then
                    MCycles<="010";TStates<="011";if MCycle="001" then TStates<="100";end if;
                    NoRead<='0';Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Arith16<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Set_Addr_To<=aNone;LDZ<='0';LDW<='0';
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';I_RETN<='0';IMode<="11";
                    Set_BusA_To<="0111";Set_BusB_To<="0111";ALU_Op<="0000";
                    if MCycle="010" then Inc_PC<='1';TStates<="101";end if;
                    if IR=x"65" or IR=x"66" then
                        if Data_Long='1' then MCycles<="101";else MCycles<="100";end if;
                        if MCycle="010" or MCycle="011" or (MCycle="100" and Data_Long='1') then
                            IncDec_16<="1111";Set_Addr_To<=aSP;
                        end if;
                        if unsigned(MCycle)>=3 then Write<='1';end if;
                    end if;
                end if;
'''+s[pos:];p.write_text(s)
