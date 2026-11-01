"""Run original rebuild, extend_r2, then this script."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal Pair_Absolute' not in s
s=s.replace('    signal SPL :', '''    signal Pair_Absolute, Pair_Read, Pair_SP : std_logic;
    signal Pair_Number : std_logic_vector(1 downto 0);
    signal Pair_Upper_Index : std_logic_vector(2 downto 0);
    signal Pair_Address_Last : integer range 3 to 4;
    signal SPL :''',1)
s=s.replace('    Extension_State<=', '''    Pair_Absolute<='1' when Extensions_Enabled='1' and (Data_Long='1' or Stream_Long='1') and IntCycle='0' and NMICycle='0' and
        ((ISet="00" and (IR=x"22" or IR=x"2A")) or (ISet="10" and IR(7 downto 6)="01" and IR(2 downto 0)="011")) else '0';
    Pair_Read<=IR(3);
    Pair_Number<="10" when ISet="00" else IR(5 downto 4);
    Pair_SP<='1' when Pair_Number="11" else '0';
    Pair_Upper_Index<=XY_State(1) & "11" when Pair_Number="10" and XY_State/="00" else Alternate & Pair_Number;
    Pair_Address_Last<=4 when Stream_Long='1' else 3;
    Extension_State<=''',1)
s=s.replace("                    if Set_Addr_To=aSP and Wide_Stack='1' then",'''                    if Pair_Absolute='1' and Set_Addr_To=aZI then
                        if Inc_WZ='1' then
                            A_BANK<=A_BANK;
                            if Data_Long='1' and A=x"FFFF" then A_BANK<=std_logic_vector(unsigned(A_BANK)+1);end if;
                        elsif Data_Long='1' and Stream_Long='1' then A_BANK<=DI_Reg;
                        else A_BANK<=x"00";end if;
                    elsif Set_Addr_To=aSP and Wide_Stack='1' then''',1)
s=s.replace("if MCycle = \"110\" and SP_Readback='0' then", "if MCycle = \"110\" and SP_Readback='0' and Pair_Absolute='0' then",1)
s=s.replace("if TState = 3 and MCycle = \"110\" and SP_Readback='0' then", "if TState = 3 and MCycle = \"110\" and SP_Readback='0' and Pair_Absolute='0' then",1)
s=s.replace("if SP_Readback='1' and MCycle=\"101\" then A<=std_logic_vector(unsigned(A)+1);", "if Pair_Absolute='1' then A<=std_logic_vector(unsigned(A)+1);elsif SP_Readback='1' and MCycle=\"101\" then A<=std_logic_vector(unsigned(A)+1);",1)
s=s.replace("                            else\n                                A(15 downto 8) <= DI_Reg;\n                                A(7 downto 0) <= TmpAddr(7 downto 0);\n                            end if;", """                            elsif Pair_Absolute='1' and Stream_Long='1' then A<=TmpAddr;
                            else
                                A(15 downto 8) <= DI_Reg;
                                A(7 downto 0) <= TmpAddr(7 downto 0);
                            end if;""",1)
s=s.replace("                if LDSPHL = '1' then\n                    SP <= unsigned(RegBusC);", """                if LDSPHL = '1' then
                    if Extensions_Enabled='1' and Data_Long='1' then SPL<=unsigned(Upper(to_integer(unsigned(RegAddrC)))) & unsigned(RegBusC);
                    else SP <= unsigned(RegBusC);end if;""",1)
s=s.replace("            if Wide_IncDec='1'", """            if Extensions_Enabled='1' and Data_Long='1' and ExchangeDH='1' and TState=3 then
                Upper(to_integer(unsigned'(Alternate & "10")))<=Upper(to_integer(unsigned'(Alternate & "01")));
                Upper(to_integer(unsigned'(Alternate & "01")))<=Upper(to_integer(unsigned'(Alternate & "10")));
            end if;
            if Pair_Absolute='1' and Pair_Read='1' and Data_Long='1' and TState=3 and to_integer(unsigned(MCycle))=Pair_Address_Last+3 then
                if Pair_SP='1' then SPL(23 downto 16)<=unsigned(DI_Reg);
                else Upper(to_integer(unsigned(Pair_Upper_Index)))<=DI_Reg;end if;
            end if;
            if Wide_IncDec='1'""",1)
s=s.replace("if Data_Long='1' and ISet=\"00\" and IR=x\"31\" then SPL", "if Data_Long='1' and ((ISet=\"00\" and IR=x\"31\") or (Pair_Absolute='1' and Pair_Read='1' and Pair_SP='1')) then SPL")
s=s.replace("                if SP_Readback='1' then BusB<=std_logic_vector(SPL(7 downto 0));", "                if SP_Readback='1' or (Pair_Absolute='1' and Data_Long='1' and Pair_SP='1') then BusB<=std_logic_vector(SPL(7 downto 0));")
s=s.replace("                if SP_Readback='1' then BusB<=std_logic_vector(SPL(15 downto 8));", "                if SP_Readback='1' or (Pair_Absolute='1' and Data_Long='1' and Pair_SP='1') then BusB<=std_logic_vector(SPL(15 downto 8));")
s=s.replace("if SP_Readback='1' then BusB<=std_logic_vector(SPL(23 downto 16));", "if Pair_Absolute='1' then\n                    if Pair_SP='1' then BusB<=std_logic_vector(SPL(23 downto 16));else BusB<=Upper(to_integer(unsigned(Pair_Upper_Index)));end if;\n                elsif SP_Readback='1' then BusB<=std_logic_vector(SPL(23 downto 16));")
# Cycles 6/7 are real transfer cycles here, not legacy indexed-displacement returns.
s=s.replace('elsif (MCycle = "111") or', "elsif (MCycle = \"111\" and Pair_Absolute='0') or")
s=s.replace('(MCycle = "110" and Mode = 1 and ISet /= "01") then', "(MCycle = \"110\" and Mode = 1 and ISet /= \"01\" and Pair_Absolute='0') then")
p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();s=s.replace('                variable IRB :', '''                variable lastaddr, countdata, cycle : integer;
                variable pairnum : std_logic_vector(1 downto 0);
                variable reading : boolean;
                variable IRB :''',1)
a=s.rindex('        end process;');s=s[:a]+'''
                -- R3 pair absolute transfers: separate immediate width and data width.
                if Ext_Active='1' and (Data_Long='1' or Stream_Long='1') and Mode=0 and IntCycle='0' and NMICycle='0' and
                   ((ISet="00" and (IR=x"22" or IR=x"2A")) or (ISet="10" and IR(7 downto 6)="01" and IR(2 downto 0)="011")) then
                    if Stream_Long='1' then lastaddr:=4;else lastaddr:=3;end if;
                    if Data_Long='1' then countdata:=3;else countdata:=2;end if;
                    if ISet="00" then pairnum:="10";else pairnum:=IR(5 downto 4);end if;
                    cycle:=to_integer(unsigned(MCycle));reading:=IR(3)='1';
                    MCycles<=std_logic_vector(to_unsigned(lastaddr+countdata,3));
                    Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';
                    Set_Addr_To<=aNone;NoRead<='0';IncDec_16<="0000";
                    if cycle=1 then TStates<="100";else TStates<="011";end if;
                    if cycle=2 then Inc_PC<='1';LDZ<='1';end if;
                    if cycle=3 then Inc_PC<='1';LDW<='1';end if;
                    if cycle=4 and lastaddr=4 then Inc_PC<='1';end if;
                    if cycle=lastaddr then
                        Set_Addr_To<=aZI;
                        if pairnum="11" then Set_BusB_To<="1000";else Set_BusB_To<='0' & pairnum & '1';end if;
                    elsif cycle>lastaddr then
                        if cycle<lastaddr+countdata then Inc_WZ<='1';Set_Addr_To<=aZI;end if;
                        if reading then
                            if cycle=lastaddr+1 then
                                Read_To_Reg<='1';if pairnum="11" then Set_BusA_To<="1000";else Set_BusA_To<='0' & pairnum & '1';end if;
                            elsif cycle=lastaddr+2 then
                                Read_To_Reg<='1';if pairnum="11" then Set_BusA_To<="1001";else Set_BusA_To<='0' & pairnum & '0';end if;
                            end if;
                        else
                            Write<='1';
                            if cycle=lastaddr+1 then
                                if pairnum="11" then Set_BusB_To<="1001";else Set_BusB_To<='0' & pairnum & '0';end if;
                            elsif cycle=lastaddr+2 then Set_BusB_To<="1110";end if;
                        end if;
                    end if;
                end if;
''' +s[a:];p.write_text(s)
