"""Stage7 native ADL interrupt entry/return, IV16 and P2 diagnostic wrapper."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text()
s=s.replace('    signal SPL :', '''    signal IRQ_Long, IRQ_Return, IRQ_IM2, Effective_IEF, IV_Read_Commit : std_logic;
    signal IRQ_Vector : unsigned(23 downto 0);
    signal I_Upper : std_logic_vector(7 downto 0);
    signal NMI_Entry_Seen : std_logic;
    signal SPL :''',1)
s=s.replace("    Ctrl_Stack<='1' when", """    IRQ_Long <= Extensions_Enabled and ADL_Mode and (IntCycle or NMICycle);
    IRQ_IM2 <= '1' when IRQ_Long='1' and IntCycle='1' and IStatus="10" else '0';
    IRQ_Return <= '1' when Extensions_Enabled='1' and ADL_Mode='1' and Instruction_Has_Width='0' and ISet="10" and
        (IR=x"45" or IR=x"4D") and IntCycle='0' and NMICycle='0' else '0';
    Effective_IEF <= '1' when ADL_Mode='1' and SetEI='1' else IntE_FF2 when IRQ_Return='1' and IR=x"45" and MCycle="100" else IntE_FF1;
    IV_Read_Commit <= '1' when Extensions_Enabled='1' and ISet="10" and IR=x"D7" and MCycle="001" and TState=4 and IntCycle='0' and NMICycle='0' else '0';
    Ctrl_Stack<='1' when IRQ_Long='1' or IRQ_Return='1' else '1' when""",1)
s=s.replace("    Ctrl_Call<=Ctrl_Stack when", "    Ctrl_Call<=Ctrl_Stack when IRQ_Long='0' and IRQ_Return='0' and (",1).replace('IR(2 downto 0)="100" else', 'IR(2 downto 0)="100") else',1)
s=s.replace("    Ctrl_Ret<=Ctrl_Stack when", "    Ctrl_Ret<='1' when IRQ_Return='1' else Ctrl_Stack when IRQ_Long='0' and (",1).replace('IR(2 downto 0)="000" else','IR(2 downto 0)="000") else',1)
s=s.replace("    Ctrl_Rst<=Ctrl_Stack when", "    Ctrl_Rst<='1' when IRQ_Long='1' else Ctrl_Stack when IRQ_Return='0' and",1)
s=s.replace('when IR=x"CD" or IR=x"C9" or Ctrl_Rst=', 'when IRQ_Return=\'1\' or IR=x"CD" or IR=x"C9" or Ctrl_Rst=',1)
s=s.replace("            Ctrl_Target<=(others=>'0');", "            I_Upper<=(others=>'0');IRQ_Vector<=(others=>'0');\n            Ctrl_Target<=(others=>'0');",1)
# The shared RST engine captures interrupted PC after entry M1, but retains a
# distinct vector-read phase for IM2. There is no legacy SPS path in native entry.
s=s.replace("if Ctrl_Rst='1' and MCycle=\"001\" and TState=4 then", "if Ctrl_Rst='1' and IRQ_Long='0' and MCycle=\"001\" and TState=4 then",1)
s=s.replace("((Ctrl_Call='1' and MCycle=\"111\") or (Ctrl_Rst='1' and MCycle=\"100\") or", "((Ctrl_Call='1' and MCycle=\"111\") or (Ctrl_Rst='1' and IRQ_IM2='0' and MCycle=\"100\") or",1)
needle="            if JP_Commit='1' then"
s=s.replace(needle,'''            if IRQ_Long='1' then
                if MCycle="001" and TState=4 then
                    Ctrl_Return<=std_logic_vector(PC);
                    if NMICycle='1' then Ctrl_Target<=x"000066";else Ctrl_Target<=x"000038";end if;
                    IRQ_Vector<=unsigned(I_Upper) & unsigned(I) & unsigned(DI_Reg);
                end if;
                if T_Res='1' and unsigned(MCycle)<=3 then
                    A<=std_logic_vector(SPL(15 downto 0));A_BANK<=std_logic_vector(SPL(23 downto 16));
                end if;
                if IRQ_IM2='1' then
                    if TState=2 and Wait_n='1' and (MCycle="101" or MCycle="110") then IRQ_Vector<=IRQ_Vector+1;end if;
                    if T_Res='1' and (MCycle="100" or MCycle="101" or MCycle="110") then
                        A<=std_logic_vector(IRQ_Vector(15 downto 0));A_BANK<=std_logic_vector(IRQ_Vector(23 downto 16));
                    end if;
                    if TState=3 then
                        if MCycle="101" then Ctrl_Target(7 downto 0)<=DI_Reg;
                        elsif MCycle="110" then Ctrl_Target(15 downto 8)<=DI_Reg;
                        elsif MCycle="111" then
                            PC<=unsigned(DI_Reg) & unsigned(Ctrl_Target(15 downto 0));
                            A<=Ctrl_Target(15 downto 0);A_BANK<=DI_Reg;
                        end if;
                    end if;
                end if;
            end if;
            if Extensions_Enabled='1' and ISet="10" and IR=x"C7" and MCycle="001" and TState=4 and IntCycle='0' and NMICycle='0' then
                I_Upper<=RegBusA(15 downto 8);I<=RegBusA(7 downto 0);
            end if;
'''+needle,1)
# Native RETN restores IEF1 at the same instruction boundary as PC commit.
s=s.replace("                if I_RETN = '1' then", "                if I_RETN = '1' then",1)
s=s.replace("            if IntCycle = '1' or NMICycle = '1' then\n                Halt_FF", "            if IRQ_Return='1' and IR=x\"45\" and MCycle=\"100\" and T_Res='1' then IntE_FF1<=IntE_FF2;end if;\n            if IntCycle = '1' or NMICycle = '1' then\n                Halt_FF",1)
s=s.replace("if ADL_Mode='0' and NMI_s", "if NMI_s",1)
s=s.replace("                                IntE_FF1 <= '0';\n                            elsif ADL_Mode='0' and (IntE_FF1 = '1'", "                                if ADL_Mode='1' then IntE_FF2<=Effective_IEF;end if;\n                                IntE_FF1 <= '0';\n                            elsif (ADL_Mode='0' or IStatus=\"01\" or IStatus=\"10\") and (Effective_IEF = '1'",1)
# Keep a second NMI edge during native entry, without changing locked Z80 behavior.
s=s.replace("            NMI_s <= '0';\n            OldNMI_n", "            NMI_s <= '0';NMI_Entry_Seen<='0';\n            OldNMI_n",1)
s=s.replace("            if NMICycle = '1' then\n                NMI_s <= '0';\n            elsif NMI_n = '0' and OldNMI_n = '1' then\n                NMI_s <= '1';\n            end if;", """            NMI_Entry_Seen<=NMICycle;
            if ADL_Mode='1' then
                if NMI_n='0' and OldNMI_n='1' then NMI_s<='1';
                elsif NMICycle='1' and NMI_Entry_Seen='0' then NMI_s<='0';end if;
            else
                if NMICycle='1' then NMI_s<='0';
                elsif NMI_n='0' and OldNMI_n='1' then NMI_s<='1';end if;
            end if;""",1)
# IV16 writes lower HL only; preserve the architecturally unspecified upper byte.
s=s.replace('Mul_Reg_Commit, LEA_Commit)','Mul_Reg_Commit, LEA_Commit, IV_Read_Commit)',1)
s=s.replace('or Mul_Reg_Commit or LEA_Commit;', 'or Mul_Reg_Commit or LEA_Commit or IV_Read_Commit;')
s=s.replace('LEA_Commit, EA_Result)', 'LEA_Commit, EA_Result, IV_Read_Commit, I_Upper, I)',1)
s=s.replace("        if LEA_Commit='1' then RegDIH", "        if IV_Read_Commit='1' then RegDIH<=I_Upper;RegDIL<=I;\n        elsif LEA_Commit='1' then RegDIH",1)
s=s.replace("elsif MCycle = MCycles and NMICycle = '1' then","elsif MCycle = MCycles and NMICycle = '1' and IRQ_Long='0' then",1)
s=s.replace("elsif MCycle = \"011\" and IntCycle = '1' and IStatus = \"10\" then","elsif MCycle = \"011\" and IntCycle = '1' and IStatus = \"10\" and IRQ_Long='0' then",1)
p.write_text(s)
# IStatus is needed to choose native IM2's seven-cycle entry.
for n in ('t80_pack_ez80.vhd','t80_mcode_ez80.vhd'):
 p=r/'fpga/G80A_eZ80'/n;s=p.read_text().replace('Flow_Cond : out std_logic;','Flow_Cond : out std_logic;\n                Interrupt_Mode : in std_logic_vector(1 downto 0);',1)
 if n.startswith('t80_mcode'):
  s=s.replace('ADL_Mode, Has_Width)', 'ADL_Mode, Has_Width, Interrupt_Mode)',1)
  s=s.replace('(IR=x"45" or IR=x"4D" or IR=x"5D" or IR=x"6D" or IR=x"7D")', '(IR=x"5D" or IR=x"6D" or IR=x"75" or IR=x"7D")',1)
  pos=s.rindex('        end process;')
  s=s[:pos]+'''
                -- R11 native ADL interrupt frame. IRQ M1 remains a real IACK.
                if Ext_Active='1' and ADL_Mode='1' and (IntCycle='1' or NMICycle='1') then
                    MCycles<="100";if IntCycle='1' and Interrupt_Mode="10" then MCycles<="111";end if;
                    TStates<="011";if MCycle="001" then TStates<="101";end if;
                    NoRead<='0';Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Halt<='0';SetEI<='0';SetDI<='0';Special_LD<="000";IMode<="11";
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';JumpE<='0';I_DJNZ<='0';I_RETN<='0';
                    Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';IncDec_16<="0000";Set_Addr_To<=aNone;Prefix<="00";
                    if unsigned(MCycle)<=3 then IncDec_16<="1111";Set_Addr_To<=aSP;end if;
                    if MCycle="010" or MCycle="011" or MCycle="100" then Write<='1';end if;
                end if;
                if Ext_Active='1' and ADL_Mode='1' and Has_Width='0' and ISet="10" and (IR=x"45" or IR=x"4D") and IntCycle='0' and NMICycle='0' then
                    MCycles<="100";TStates<="011";if MCycle="001" then TStates<="101";end if;
                    NoRead<='0';Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Jump<='0';I_RETN<='0';
                    Inc_PC<='0';Inc_WZ<='0';LDZ<='0';LDW<='0';IncDec_16<="0000";Set_Addr_To<=aNone;
                    if unsigned(MCycle)<=3 then Set_Addr_To<=aSP;end if;
                    if unsigned(MCycle)>=2 then IncDec_16<="0111";end if;
                end if;
                if Ext_Active='1' and ISet="10" and (IR=x"C7" or IR=x"D7") and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="101";NoRead<='1';Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Inc_PC<='0';IncDec_16<="0000";Set_Addr_To<=aNone;Set_BusA_To<="0100";Special_LD<="000";
                end if;
                -- Mode-bearing RETI.L/RETN.L frames remain stage8 work.
                if Ext_Active='1' and Has_Width='1' and ISet="10" and (IR=x"45" or IR=x"4D") and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="100";Halt<='1';NoRead<='1';Write<='0';Jump<='0';I_RETN<='0';
                    IncDec_16<="0000";Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Set_Addr_To<=aNone;
                end if;
'''+s[pos:]
 p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text().replace('Flow_Cond=>Flow_Cond,','Flow_Cond=>Flow_Cond, Interrupt_Mode=>IStatus,',1);p.write_text(s)

from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text()
s=s.replace('signal NMI_Entry_Seen : std_logic;', 'signal NMI_Accept : std_logic;')
s=s.replace("NMI_s <= '0';NMI_Entry_Seen<='0';", "NMI_s <= '0';")
s=s.replace('            NMI_Entry_Seen<=NMICycle;','')
s=s.replace("elsif NMICycle='1' and NMI_Entry_Seen='0' then", "elsif NMI_Accept='1' then")
s=s.replace('    IRQ_Long <=', '''    -- Acknowledge exactly at the dispatch boundary; a new edge at that same
    -- clock wins in the input latch and remains pending for a subsequent entry.
    NMI_Accept<='1' when NMI_s='1' and Prefix="00" and Width_Pending='0' and BusReq_s='0' and T_Res='1' and NextIs_XY_Fetch='0' and
        not ((MCycle="111" and Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0') or
             (MCycle="110" and Mode=1 and ISet/="01" and Pair_Absolute='0' and EX_SP_Long='0' and Ctrl_Stack='0')) and
        (MCycle=MCycles or No_BTR='1' or (MCycle="010" and I_DJNZ='1' and IncDecZ='1')) else '0';
    IRQ_Long <=''',1)
p.write_text(s)
