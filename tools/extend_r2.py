"""Run rebuild_from_t80.py, then this script. Only data widths change; PC/IRQ remain Z80."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal Wide_Stack' not in s
# Incoming opcode belongs to the previous PREFIX output, not the previous ISet.
# A suffix immediately after a completed ED instruction is again a base opcode.
s=s.replace('if ISet="00" and (DInst=x"40"', 'if Prefix/="10" and Prefix/="01" and (DInst=x"40"',1)
s=s.replace('    signal SPL :', '''    signal Wide_Stack, Wide_IncDec : std_logic;
    signal Stack_Upper_Index : std_logic_vector(2 downto 0);
    signal SPL :''',1)
s=s.replace('    Extension_State<=', '''    Wide_Stack<='1' when Extensions_Enabled='1' and Data_Long='1' and ISet="00" and
        IntCycle='0' and NMICycle='0' and IR(7 downto 6)="11" and
        (IR(3 downto 0)="0101" or IR(3 downto 0)="0001") else '0';
    Wide_IncDec<='1' when Extensions_Enabled='1' and Data_Long='1' and ISet="00" and
        IntCycle='0' and NMICycle='0' and IR(7 downto 6)="00" and
        (IR(3 downto 0)="0011" or IR(3 downto 0)="1011") else '0';
    Stack_Upper_Index<=XY_State(1) & "11" when IR(5 downto 4)="10" and XY_State/="00" else Alternate & IR(5 downto 4);
    Extension_State<=''',1)
s=s.replace("                    if Set_Addr_To=aBC",'''                    if Set_Addr_To=aSP and Wide_Stack='1' then
                        A_BANK<=std_logic_vector(SPL(23 downto 16));
                    elsif Set_Addr_To=aBC''',1)
s=s.replace('A <= std_logic_vector(SP);',"if Wide_Stack='1' then A<=std_logic_vector(SPL(15 downto 0));else A <= std_logic_vector(SP);end if;",1)
s=s.replace("                        if IncDec_16(3) = '1' then\n                            SP <= SP - 1;",'''                        if Wide_Stack='1' or Wide_IncDec='1' then
                            if IncDec_16(3)='1' then SPL<=SPL-1;else SPL<=SPL+1;end if;
                        elsif IncDec_16(3) = '1' then
                            SP <= SP - 1;''',1)
# Upper INC/DEC changes at exactly the original pair's lower16 write edge.
s=s.replace("            if TState=3 and IntCycle='0'",'''            if Wide_IncDec='1' and MCycle="001" and TState=3 and IR(5 downto 4)/="11" then
                if IncDec_16(3)='1' and RegBusA=x"0000" then
                    Upper(to_integer(unsigned(RegAddrA)))<=std_logic_vector(unsigned(Upper(to_integer(unsigned(RegAddrA))))-1);
                elsif IncDec_16(3)='0' and RegBusA=x"FFFF" then
                    Upper(to_integer(unsigned(RegAddrA)))<=std_logic_vector(unsigned(Upper(to_integer(unsigned(RegAddrA))))+1);
                end if;
            end if;
            if Wide_Stack='1' and IR(3 downto 0)="0001" and MCycle="100" and TState=3 and IR(5 downto 4)/="11" then
                Upper(to_integer(unsigned(Stack_Upper_Index)))<=DI_Reg;
            end if;
            if TState=3 and IntCycle='0' ''',1)
s=s.replace("                if I_RLD = '1' then",'''                if Wide_Stack='1' and IR(3 downto 0)="0101" and MCycle="010" then
                    if IR(5 downto 4)="11" then DO<=x"00";
                    else DO<=Upper(to_integer(unsigned(Stack_Upper_Index)));end if;
                end if;
                if I_RLD = '1' then''',1)
p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();at=s.rindex('        end process;')
s=s[:at]+'''
                -- R2 explicit long PUSH/POP. SPL only; never changes SPS or PC.
                if Ext_Active='1' and Data_Long='1' and ISet="00" and Mode=0 and IntCycle='0' and NMICycle='0' and
                   IR(7 downto 6)="11" and (IR(3 downto 0)="0101" or IR(3 downto 0)="0001") then
                    MCycles<="100"; Write<='0';Read_To_Reg<='0';IncDec_16<="0000";Set_Addr_To<=aNone;
                    TStates<="011"; if MCycle="001" then TStates<="100";end if;
                    if IR(3 downto 0)="0101" then
                        case to_integer(unsigned(MCycle)) is
                        when 1 => TStates<="101";IncDec_16<="1111";Set_Addr_To<=aSP;
                            if DPair="11" then Set_BusB_To<="0111";else Set_BusB_To<='0' & DPair & '0';end if;
                        when 2 => Write<='1';IncDec_16<="1111";Set_Addr_To<=aSP;
                            if DPair="11" then Set_BusB_To<="0111";else Set_BusB_To<='0' & DPair & '0';end if;
                        when 3 => Write<='1';IncDec_16<="1111";Set_Addr_To<=aSP;
                            if DPair="11" then Set_BusB_To<="1011";else Set_BusB_To<='0' & DPair & '1';end if;
                        when 4 => Write<='1';
                        when others=>null;
                        end case;
                    else
                        case to_integer(unsigned(MCycle)) is
                        when 1=>Set_Addr_To<=aSP;
                        when 2=>IncDec_16<="0111";Set_Addr_To<=aSP;Read_To_Reg<='1';
                            if DPair="11" then Set_BusA_To<="1011";else Set_BusA_To<='0' & DPair & '1';end if;
                        when 3=>IncDec_16<="0111";Set_Addr_To<=aSP;Read_To_Reg<='1';
                            if DPair="11" then Set_BusA_To<="0111";else Set_BusA_To<='0' & DPair & '0';end if;
                        when 4=>IncDec_16<="0111";
                        when others=>null;
                        end case;
                    end if;
                end if;
''' + s[at:];p.write_text(s)
