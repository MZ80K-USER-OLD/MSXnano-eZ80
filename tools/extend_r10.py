"""Stage6: native ADL flow, shared condition decoder and held 3-byte frames.
Mixed suffix CALL/RET/RST and ADL IRQ remain guarded for stages8 and7.
"""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
# Reuse the existing mcode condition function through one output; expose the
# captured width-prefix presence so native frames cannot be confused with mixed frames.
for name in ('t80_pack_ez80.vhd','t80_mcode_ez80.vhd'):
 p=r/'fpga/G80A_eZ80'/name;s=p.read_text()
 s=s.replace('Ext_Active, Data_Long, Stream_Long, ADL_Mode : in std_logic;', 'Ext_Active, Data_Long, Stream_Long, ADL_Mode, Has_Width : in std_logic;\n                Flow_Cond : out std_logic;',1)
 if name.startswith('t80_mcode'):
  s=s.replace('Stream_Long, ADL_Mode)', 'Stream_Long, ADL_Mode, Has_Width)',1)
  s=s.replace('                MCycles <= "001";', '''                if is_cc_true(F,to_bitvector(IR(5 downto 3))) then Flow_Cond<='1';else Flow_Cond<='0';end if;
                MCycles <= "001";''',1)
  # Remove only the stage6 ADL guard, retaining the independent RETI/RETN guard.
  a=s.index('                -- Stage 6 is not yet implemented:');z=s.index('                if ADL_Mode=\'1\' and ISet="10"',a);s=s[:a]+s[z:]
  # JP immediate shares the R9 transition and address fetch for true/false conditions.
  s=s.replace('ISet="00" and IR=x"C3" and Data_Long=Stream_Long', 'ISet="00" and (IR=x"C3" or (IR(7 downto 6)="11" and IR(2 downto 0)="010")) and Data_Long=Stream_Long',1)
  pos=s.rindex('        end process;')
  s=s[:pos]+'''
                -- Native ADL CALL/RET/RST use only a 3-byte SPL frame, no mode byte.
                if Ext_Active='1' and ADL_Mode='1' and Has_Width='0' and ISet="00" and IntCycle='0' and NMICycle='0' and
                    (IR=x"CD" or IR=x"C9" or (IR(7 downto 6)="11" and
                     (IR(2 downto 0)="100" or IR(2 downto 0)="000" or IR(2 downto 0)="111"))) then
                    TStates<="011";if MCycle="001" then TStates<="101";end if;
                    NoRead<='0';Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';JumpE<='0';I_DJNZ<='0';
                    Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';IncDec_16<="0000";Set_Addr_To<=aNone;
                    if IR=x"CD" or IR(2 downto 0)="100" then
                        -- M2..M4 target bytes, M5..M7 return PC bytes (upper first).
                        if IR=x"CD" or is_cc_true(F,to_bitvector(IR(5 downto 3))) then
                            MCycles<="111";
                            if MCycle="100" or MCycle="101" or MCycle="110" then IncDec_16<="1111";Set_Addr_To<=aSP;end if;
                            if unsigned(MCycle)>=5 then Write<='1';end if;
                        else MCycles<="100";end if;
                        if unsigned(MCycle)>=2 and unsigned(MCycle)<=4 then Inc_PC<='1';end if;
                    elsif IR=x"C9" or IR(2 downto 0)="000" then
                        if IR=x"C9" or is_cc_true(F,to_bitvector(IR(5 downto 3))) then
                            MCycles<="100";
                            if unsigned(MCycle)<=3 then Set_Addr_To<=aSP;end if;
                            if unsigned(MCycle)>=2 then IncDec_16<="0111";end if;
                        else MCycles<="001";NoRead<='1';end if;
                    else
                        MCycles<="100";
                        if unsigned(MCycle)<=3 then IncDec_16<="1111";Set_Addr_To<=aSP;end if;
                        if unsigned(MCycle)>=2 then Write<='1';end if;
                    end if;
                end if;
                -- Mixed CALL/RET/RST suffix frames belong to stage8, not this native path.
                if Ext_Active='1' and Has_Width='1' and ISet="00" and
                    (IR=x"CD" or IR=x"C9" or (IR(7 downto 6)="11" and
                     (IR(2 downto 0)="100" or IR(2 downto 0)="000" or IR(2 downto 0)="111"))) then
                    MCycles<="001";TStates<="100";Halt<='1';NoRead<='1';Write<='0';
                    Jump<='0';Call<='0';RstP<='0';IncDec_16<="0000";Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Set_Addr_To<=aNone;
                end if;
'''+s[pos:]
 p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal Ctrl_Stack' not in s
s=s.replace('    signal SPL :', '''    signal Ctrl_Stack, Ctrl_Call, Ctrl_Ret, Ctrl_Rst, Ctrl_Taken, Flow_Cond : std_logic;
    signal Ctrl_Target, Ctrl_Return : std_logic_vector(23 downto 0);
    signal SPL :''',1)
s=s.replace('ADL_Mode=>ADL_Mode,','ADL_Mode=>ADL_Mode, Has_Width=>Instruction_Has_Width, Flow_Cond=>Flow_Cond,',1)
s=s.replace('    Extension_State<=', '''    Ctrl_Stack<='1' when Extensions_Enabled='1' and ADL_Mode='1' and Instruction_Has_Width='0' and ISet="00" and
        IntCycle='0' and NMICycle='0' and (IR=x"CD" or IR=x"C9" or (IR(7 downto 6)="11" and
        (IR(2 downto 0)="100" or IR(2 downto 0)="000" or IR(2 downto 0)="111"))) else '0';
    Ctrl_Call<=Ctrl_Stack when IR=x"CD" or IR(2 downto 0)="100" else '0';
    Ctrl_Ret<=Ctrl_Stack when IR=x"C9" or IR(2 downto 0)="000" else '0';
    Ctrl_Rst<=Ctrl_Stack when IR(2 downto 0)="111" else '0';
    Ctrl_Taken<='1' when IR=x"CD" or IR=x"C9" or Ctrl_Rst='1' else Flow_Cond;
    Extension_State<=''',1)
s=s.replace("            ADL_Mode<='0';", "            Ctrl_Target<=(others=>'0');Ctrl_Return<=(others=>'0');\n            ADL_Mode<='0';",1)
s=s.replace('and ISet="00" and IR=x"C3" and', 'and ISet="00" and (IR=x"C3" or (IR(7 downto 6)="11" and IR(2 downto 0)="010")) and',1)
s=s.replace("when JP_Immediate='1' and TState=3 and", "when JP_Immediate='1' and (IR=x\"C3\" or Flow_Cond='1') and TState=3 and",1)
# Protect all inherited indexed M6/M7 special handling on the new 7-cycle CALL.
s=s.replace("Pair_Absolute='0' and EX_SP_Long='0'", "Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0'")
s=s.replace('(MCycle = "110") then', '(MCycle = "110" and Ctrl_Stack=\'0\') then')
s=s.replace("Wide_Stack='1' or PEA_Long='1'", "Wide_Stack='1' or PEA_Long='1' or Ctrl_Stack='1'")
s=s.replace("Wide_IncDec='1' or PEA_Long='1'", "Wide_IncDec='1' or PEA_Long='1' or Ctrl_Stack='1'")
s=s.replace('                        PC <= resize(unsigned(RegBusC),24);', '''                        if Extensions_Enabled='1' and ISet="00" and IR=x"E9" then
                            if Data_Long='1' then
                                PC<=unsigned(Upper(to_integer(unsigned(RegAddrC)))) & unsigned(RegBusC);
                                A_BANK<=Upper(to_integer(unsigned(RegAddrC)));ADL_Mode<='1';
                            else PC<=resize(unsigned(RegBusC),24);A_BANK<=x"00";ADL_Mode<='0';end if;
                        else PC <= resize(unsigned(RegBusC),24);end if;''',1)
s=s.replace("            if JP_Commit='1' then", '''            if Ctrl_Call='1' and TState=3 then
                case MCycle is
                when "010"=>Ctrl_Target(7 downto 0)<=DI_Reg;
                when "011"=>Ctrl_Target(15 downto 8)<=DI_Reg;
                when "100"=>Ctrl_Target(23 downto 16)<=DI_Reg;Ctrl_Return<=std_logic_vector(PC);
                when others=>null;
                end case;
            end if;
            if Ctrl_Rst='1' and MCycle="001" and TState=4 then
                Ctrl_Return<=std_logic_vector(PC);Ctrl_Target<=x"0000" & "00" & IR(5 downto 3) & "000";
            end if;
            if Ctrl_Ret='1' and TState=3 then
                if MCycle="010" then Ctrl_Target(7 downto 0)<=DI_Reg;
                elsif MCycle="011" then Ctrl_Target(15 downto 8)<=DI_Reg;end if;
            end if;
            if Ctrl_Taken='1' and TState=3 and
                ((Ctrl_Call='1' and MCycle="111") or (Ctrl_Rst='1' and MCycle="100") or (Ctrl_Ret='1' and MCycle="100")) then
                if Ctrl_Ret='1' then
                    PC<=unsigned(DI_Reg) & unsigned(Ctrl_Target(15 downto 0));
                    A<=Ctrl_Target(15 downto 0);A_BANK<=DI_Reg;
                else PC<=unsigned(Ctrl_Target);A<=Ctrl_Target(15 downto 0);A_BANK<=Ctrl_Target(23 downto 16);end if;
            end if;
            if JP_Commit='1' then''',1)
s=s.replace("                if PEA_Active='1' then", '''                if Ctrl_Call='1' then
                    if MCycle="101" then DO<=Ctrl_Return(23 downto 16);
                    elsif MCycle="110" then DO<=Ctrl_Return(15 downto 8);
                    elsif MCycle="111" then DO<=Ctrl_Return(7 downto 0);end if;
                elsif Ctrl_Rst='1' then
                    if MCycle="010" then DO<=Ctrl_Return(23 downto 16);
                    elsif MCycle="011" then DO<=Ctrl_Return(15 downto 8);
                    elsif MCycle="100" then DO<=Ctrl_Return(7 downto 0);end if;
                end if;
                if PEA_Active='1' then''',1)
p.write_text(s)
