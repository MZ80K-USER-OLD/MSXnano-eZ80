"""R7: shared registered 8x8 MLT. Apply after extend_r6."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal Mul_Active' not in s
s=s.replace('    signal SPL :', '''    signal Mul_Active, Mul_Commit, Mul_Reg_Commit : std_logic;
    signal Mul_Target : std_logic_vector(2 downto 0);
    signal Mul_Operand : unsigned(15 downto 0);
    signal Mul_Left, Mul_Right : unsigned(7 downto 0);
    signal Mul_Product : unsigned(15 downto 0);
    attribute syn_dspstyle : string;
    attribute syn_dspstyle of Mul_Product : signal is "dsp";
    signal SPL :''',1)
s=s.replace('    Extension_State<=', '''    Mul_Active<='1' when Mode=0 and Extensions_Enabled='1' and ISet="10" and
        IR(7 downto 6)="01" and IR(3 downto 0)="1100" and IntCycle='0' and NMICycle='0' else '0';
    Mul_Target<=Alternate & IR(5 downto 4);
    Mul_Operand<=SPL(15 downto 0) when IR(5 downto 4)="11" and Data_Long='1' else
        SP when IR(5 downto 4)="11" else unsigned(RegBusA);
    Mul_Commit<='1' when Mul_Active='1' and MCycle="001" and TState=7 else '0';
    Mul_Reg_Commit<=Mul_Commit when IR(5 downto 4)/="11" else '0';
    Extension_State<=''',1)
s=s.replace("            Instruction_Has_Width<=", "            Mul_Left<=(others=>'0');Mul_Right<=(others=>'0');Mul_Product<=(others=>'0');\n            Instruction_Has_Width<=",1)
s=s.replace("            if Arith_Long='1' and MCycle=", '''            -- Capture source before computing: no combinational CPU bus reaches DSP output.
            if Mul_Active='1' and MCycle="001" then
                if TState=4 then Mul_Left<=Mul_Operand(15 downto 8);Mul_Right<=Mul_Operand(7 downto 0);end if;
                if TState=5 then Mul_Product<=Mul_Left*Mul_Right;end if;
            end if;
            if Mul_Commit='1' and IR(5 downto 4)="11" then
                if Data_Long='1' then SPL(15 downto 0)<=Mul_Product;else SP<=Mul_Product;end if;
            end if;
            if Arith_Long='1' and MCycle=''',1)
s=s.replace('    RegAddrA <= Arith_Target',"    RegAddrA <= Mul_Target when Mul_Active='1' else Arith_Target",1)
s=s.replace('Wait_n, EX_SP_Result_WE, Arith_Commit)', 'Wait_n, EX_SP_Result_WE, Arith_Commit, Mul_Reg_Commit)')
s=s.replace('Wait_n, EX_SP_Result_WE, EX_SP_Read, Arith_Commit, Arith_Result)', 'Wait_n, EX_SP_Result_WE, EX_SP_Read, Arith_Commit, Arith_Result, Mul_Reg_Commit, Mul_Product)')
s=s.replace('RegWEH <= EX_SP_Result_WE or Arith_Commit;', 'RegWEH <= EX_SP_Result_WE or Arith_Commit or Mul_Reg_Commit;').replace('RegWEL <= EX_SP_Result_WE or Arith_Commit;', 'RegWEL <= EX_SP_Result_WE or Arith_Commit or Mul_Reg_Commit;')
s=s.replace("        if Arith_Commit='1' then RegDIH", "        if Mul_Reg_Commit='1' then RegDIH<=std_logic_vector(Mul_Product(15 downto 8));RegDIL<=std_logic_vector(Mul_Product(7 downto 0));\n        elsif Arith_Commit='1' then RegDIH",1)
p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();pos=s.rindex('        end process;')
s=s[:pos]+'''
                -- MLT replaces only the four NEG aliases while the extension gate is open.
                -- One captured 8x8 multiply is committed at T7, flags and upper byte preserved.
                if Ext_Active='1' and Mode=0 and ISet="10" and IR(7 downto 6)="01" and
                    IR(3 downto 0)="1100" and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="111";NoRead<='1';Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Arith16<='0';Save_ALU<='0';
                    Set_Addr_To<=aNone;Set_BusA_To<="0111";Set_BusB_To<="0111";ALU_Op<="0000";
                end if;
'''+s[pos:];p.write_text(s)
