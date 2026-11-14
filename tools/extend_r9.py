"""R9 stage 5: persistent ADL + PC24/fetch. JP immediate is the transition bridge.
Remaining ADL control transfers trap as HALT until stage 6; ADL IRQ is gated until stage 7.
"""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();assert 'signal ADL_Mode' not in s
s=s.replace('    signal SP, PC           : unsigned(15 downto 0);', '    signal SP : unsigned(15 downto 0);\n    signal PC, PC_Increment : unsigned(23 downto 0);')
s=s.replace('    signal SPL :', '''    signal ADL_Mode, JP_Immediate, JP_Commit : std_logic;
    signal SPL :''',1)
s=s.replace('\nbegin\n', '''
    function PC_Width(value : unsigned(23 downto 0); wide : std_logic) return unsigned is
        variable v : unsigned(23 downto 0);
    begin
        v:=value;if wide='0' then v(23 downto 16):=(others=>'0');end if;return v;
    end function;
begin
''',1)
s=s.replace('Ext_Active=>Extensions_Enabled, Data_Long=>Data_Long, Stream_Long=>Stream_Long,', 'Ext_Active=>Extensions_Enabled, Data_Long=>Data_Long, Stream_Long=>Stream_Long, ADL_Mode=>ADL_Mode,',1)
s=s.replace('    Extension_State<=', '''    PC_Increment<=PC+1;
    JP_Immediate<='1' when Extensions_Enabled='1' and ISet="00" and IR=x"C3" and
        Data_Long=Stream_Long and IntCycle='0' and NMICycle='0' else '0';
    JP_Commit<='1' when JP_Immediate='1' and TState=3 and
        ((Stream_Long='1' and MCycle="100") or (Stream_Long='0' and MCycle="011")) else '0';
    Extension_State<=''',1)
s=s.replace("            Instruction_Has_Width<=", "            ADL_Mode<='0';\n            Instruction_Has_Width<=",1)
s=s.replace('PC <= PC + 1;', 'PC <= PC_Width(PC_Increment,ADL_Mode);')
s=s.replace('PC <= unsigned(RegBusC);', 'PC <= resize(unsigned(RegBusC),24);')
s=s.replace('PC <= unsigned(TmpAddr);', 'PC <= resize(unsigned(TmpAddr),24);')
s=s.replace('PC <= "0000000001100110";', 'PC <= to_unsigned(16#66#,24);')
s=s.replace('std_logic_vector(PC)', 'std_logic_vector(PC(15 downto 0))')
s=s.replace('PC <= unsigned(signed(PC) + signed(DI_Reg));', 'PC <= PC_Width(unsigned(signed(PC) + signed(DI_Reg)),ADL_Mode);')
s=s.replace('PC<=PC-3;', 'PC<=PC_Width(PC-3,ADL_Mode);').replace('PC <= PC - 2;', 'PC <= PC_Width(PC-2,ADL_Mode);')
s=s.replace("                A_BANK<=x\"00\";\n                if Extensions_Enabled", '''                A_BANK<=x"00";
                -- Instruction stream stays PC24 even for a short data-width prefix.
                if ADL_Mode='1' and (Set_Addr_To=aNone or (Set_Addr_To=aXY and NextIs_XY_Fetch='1')) then
                    A_BANK<=std_logic_vector(PC(23 downto 16));
                end if;
                if Extensions_Enabled''',1)
s=s.replace("if DO=x\"00\" then Extensions_Enabled<='0'; Unlock_Armed<='0';", "if DO=x\"00\" then\n                        if ADL_Mode='0' then Extensions_Enabled<='0';end if;Unlock_Armed<='0';",1)
s=s.replace("                            Data_Long<=Width_Pending and Width_Code(3);\n                            Stream_Long<=Width_Pending and Width_Code(4);", "                            if Width_Pending='1' then Data_Long<=Width_Code(3);Stream_Long<=Width_Code(4);\n                            else Data_Long<=ADL_Mode;Stream_Long<=ADL_Mode;end if;",1)
s=s.replace("            -- The displacement is stable", '''            if JP_Commit='1' then
                if Stream_Long='1' then
                    PC<=(unsigned(DI_Reg) & unsigned(TmpAddr));A<=TmpAddr;A_BANK<=DI_Reg;ADL_Mode<='1';
                else
                    PC<=(to_unsigned(0,8) & unsigned(DI_Reg) & unsigned(TmpAddr(7 downto 0)));
                    A<=DI_Reg & TmpAddr(7 downto 0);A_BANK<=x"00";ADL_Mode<='0';
                end if;
            end if;
            -- The displacement is stable''',1)
s=s.replace("if NMI_s = '1' and Prefix =", "if ADL_Mode='0' and NMI_s = '1' and Prefix =",1)
s=s.replace("elsif (IntE_FF1 = '1' and INT_s = '1') and Prefix =", "elsif ADL_Mode='0' and (IntE_FF1 = '1' and INT_s = '1') and Prefix =",1)
p.write_text(s)
for name in ['t80_mcode_ez80.vhd','t80_pack_ez80.vhd']:
 p=r/'fpga/G80A_eZ80'/name;s=p.read_text();s=s.replace('Ext_Active, Data_Long, Stream_Long : in std_logic;', 'Ext_Active, Data_Long, Stream_Long, ADL_Mode : in std_logic;',1)
 if name.startswith('t80_mcode'):
  s=s.replace('XY_State, Ext_Active, Data_Long, Stream_Long)', 'XY_State, Ext_Active, Data_Long, Stream_Long, ADL_Mode)',1)
  pos=s.rindex('        end process;')
  s=s[:pos]+'''
                -- Stage-5 transition: JP.LIL enters ADL, JP.SIS returns to Z80.
                if Ext_Active='1' and ISet="00" and IR=x"C3" and Data_Long=Stream_Long and IntCycle='0' and NMICycle='0' then
                    if Stream_Long='1' then MCycles<="100";else MCycles<="011";end if;
                    TStates<="011";if MCycle="001" then TStates<="100";end if;
                    NoRead<='0';Write<='0';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Set_Addr_To<=aNone;Jump<='0';Inc_PC<='0';LDZ<='0';LDW<='0';IncDec_16<="0000";
                    if MCycle="010" then Inc_PC<='1';LDZ<='1';end if;
                    if MCycle="011" then Inc_PC<='1';LDW<='1';end if;
                    if MCycle="100" then Inc_PC<='1';end if;
                end if;
                -- Stage 6 is not yet implemented: never fall back to a 16-bit call/return
                -- frame while in ADL. Unsupported control transfers stop without a write.
                if ADL_Mode='1' and ISet="00" and
                    (IR=x"10" or IR=x"18" or IR=x"20" or IR=x"28" or IR=x"30" or IR=x"38" or IR=x"E9" or
                     IR=x"CD" or IR=x"C9" or (IR(7 downto 6)="11" and
                        (IR(2 downto 0)="100" or IR(2 downto 0)="000" or IR(2 downto 0)="111" or IR(2 downto 0)="010"))) then
                    MCycles<="001";TStates<="100";Halt<='1';NoRead<='1';Write<='0';
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';Inc_PC<='0';IncDec_16<="0000";
                    Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Set_Addr_To<=aNone;
                end if;
                if ADL_Mode='1' and ISet="10" and (IR=x"45" or IR=x"4D" or IR=x"5D" or IR=x"6D" or IR=x"7D") then
                    MCycles<="001";TStates<="100";Halt<='1';NoRead<='1';Write<='0';Jump<='0';I_RETN<='0';
                    IncDec_16<="0000";Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';Set_Addr_To<=aNone;
                end if;
'''+s[pos:]
 p.write_text(s)
