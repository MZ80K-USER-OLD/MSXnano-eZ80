"""Apply after original rebuild and extend_r2/r3/r4. One registered 24-bit arithmetic path."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal Arith_Long' not in s
s=s.replace('    signal SPL :', '''    signal Arith_Long, Arith_Commit, Arith_Sub, Arith_Carry : std_logic;
    signal Arith_Target, Arith_Source : std_logic_vector(2 downto 0);
    signal Arith_Left, Arith_Right : unsigned(23 downto 0);
    signal Arith_Flags : std_logic_vector(7 downto 0);
    signal Arith_Sub_Latched, Arith_Carry_Latched, Arith_Is_ADD : std_logic;
    signal Arith_Xor_Right : unsigned(23 downto 0);
    signal Arith_Sum : unsigned(24 downto 0);
    signal Arith_Result : unsigned(23 downto 0);
    signal Arith_Overflow, Arith_Half, Arith_Carry_Out : std_logic;
    signal SPL :''',1)
s=s.replace('    Extension_State<=', '''    Arith_Long<='1' when Mode=0 and Extensions_Enabled='1' and Data_Long='1' and IntCycle='0' and NMICycle='0' and
        ((ISet="00" and IR(7 downto 6)="00" and IR(3 downto 0)="1001") or
         (ISet="10" and IR(7 downto 6)="01" and IR(2 downto 0)="010")) else '0';
    Arith_Target<=XY_State(1) & "11" when ISet="00" and XY_State/="00" else Alternate & "10";
    Arith_Source<=Arith_Target when IR(5 downto 4)="10" else Alternate & IR(5 downto 4);
    Arith_Sub<='1' when ISet="10" and IR(3)='0' else '0';
    Arith_Carry<=F(Flag_C) when ISet="10" else '0';
    Arith_Commit<='1' when Arith_Long='1' and MCycle="001" and TState=7 else '0';
    -- Both operands and flags are captured at T4 and held through the T7 commit.
    -- Addition and subtraction share this single adder; subtraction complements B.
    Arith_Xor_Right<=not Arith_Right when Arith_Sub_Latched='1' else Arith_Right;
    Arith_Sum<=resize(Arith_Left,25)+resize(Arith_Xor_Right,25)+to_unsigned(1,25) when (Arith_Carry_Latched xor Arith_Sub_Latched)='1'
        else resize(Arith_Left,25)+resize(Arith_Xor_Right,25);
    Arith_Result<=Arith_Sum(23 downto 0);
    Arith_Half<=Arith_Left(12) xor Arith_Right(12) xor Arith_Result(12);
    Arith_Carry_Out<=Arith_Sum(24) xor Arith_Sub_Latched;
    Arith_Overflow<=(not (Arith_Left(23) xor Arith_Right(23) xor Arith_Sub_Latched)) and (Arith_Left(23) xor Arith_Result(23));
    Extension_State<=''',1)
s=s.replace("            EX_SP_Read<=", "            Arith_Left<=(others=>'0');Arith_Right<=(others=>'0');Arith_Flags<=(others=>'0');\n            Arith_Sub_Latched<='0';Arith_Carry_Latched<='0';Arith_Is_ADD<='0';\n            EX_SP_Read<=",1)
s=s.replace("            if EX_SP_Long='1' and TState=3 then", '''            if Arith_Long='1' and MCycle="001" and TState=4 then
                Arith_Left<=unsigned(Upper(to_integer(unsigned(Arith_Target)))) & unsigned(RegBusA);
                if IR(5 downto 4)="11" then Arith_Right<=SPL;
                else Arith_Right<=unsigned(Upper(to_integer(unsigned(Arith_Source)))) & unsigned(RegBusB);end if;
                Arith_Flags<=F;Arith_Sub_Latched<=Arith_Sub;Arith_Carry_Latched<=Arith_Carry;
                if ISet="00" then Arith_Is_ADD<='1';else Arith_Is_ADD<='0';end if;
            end if;
            if Arith_Commit='1' then
                Upper(to_integer(unsigned(Arith_Target)))<=std_logic_vector(Arith_Result(23 downto 16));
            end if;
            if EX_SP_Long='1' and TState=3 then''',1)
# Commit arithmetic flags after any inherited ALU flag assignment.
s=s.replace("            if TState = 1 and Auto_Wait_t1 = '0' then\n                DO <= BusB;", '''            if Arith_Commit='1' then
                F(Flag_H)<=Arith_Half;F(Flag_N)<=Arith_Sub_Latched;F(Flag_C)<=Arith_Carry_Out;
                F(Flag_X)<=Arith_Result(19);F(Flag_Y)<=Arith_Result(21);
                if Arith_Is_ADD='1' then
                    F(Flag_S)<=Arith_Flags(Flag_S);F(Flag_Z)<=Arith_Flags(Flag_Z);F(Flag_P)<=Arith_Flags(Flag_P);
                else
                    F(Flag_S)<=Arith_Result(23);F(Flag_P)<=Arith_Overflow;
                    if Arith_Result=0 then F(Flag_Z)<='1';else F(Flag_Z)<='0';end if;
                end if;
            end if;
            if TState = 1 and Auto_Wait_t1 = '0' then
                DO <= BusB;''',1)
s=s.replace("    RegAddrA <= EX_SP_Index", "    RegAddrA <= Arith_Target when Arith_Long='1' else EX_SP_Index",1)
s=s.replace('    RegAddrB <=', "    RegAddrB <= Arith_Source when Arith_Long='1' else",1)
s=s.replace('Wait_n, EX_SP_Result_WE)', 'Wait_n, EX_SP_Result_WE, Arith_Commit)')
s=s.replace('Wait_n, EX_SP_Result_WE, EX_SP_Read)', 'Wait_n, EX_SP_Result_WE, EX_SP_Read, Arith_Commit, Arith_Result)')
s=s.replace('        RegWEH <= EX_SP_Result_WE;', '        RegWEH <= EX_SP_Result_WE or Arith_Commit;',1).replace('        RegWEL <= EX_SP_Result_WE;', '        RegWEL <= EX_SP_Result_WE or Arith_Commit;',1)
s=s.replace("        if EX_SP_Result_WE='1' then RegDIH", "        if Arith_Commit='1' then RegDIH<=std_logic_vector(Arith_Result(15 downto 8));RegDIL<=std_logic_vector(Arith_Result(7 downto 0));\n        elsif EX_SP_Result_WE='1' then RegDIH",1)
p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();a=s.rindex('        end process;')
s=s[:a]+'''
                -- R5 long ADD/ADC/SBC. Internal T4 operand capture, T7 atomic result.
                -- Short and locked profiles retain the original 8-bit ALU schedule.
                if Ext_Active='1' and Data_Long='1' and Mode=0 and IntCycle='0' and NMICycle='0' and
                    ((ISet="00" and IR(7 downto 6)="00" and IR(3 downto 0)="1001") or
                     (ISet="10" and IR(7 downto 6)="01" and IR(2 downto 0)="010")) then
                    MCycles<="001";TStates<="111";NoRead<='1';Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Arith16<='0';Save_ALU<='0';
                    Set_Addr_To<=aNone;Set_BusA_To<="0111";Set_BusB_To<="0111";ALU_Op<="0000";
                end if;
''' +s[a:];p.write_text(s)
