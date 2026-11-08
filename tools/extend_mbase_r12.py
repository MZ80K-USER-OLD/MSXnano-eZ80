from pathlib import Path
r=Path(__file__).resolve().parent.parent
assert (r/'fpga/G80A_eZ80/t80_ez80.vhd').read_bytes()==(r/'doc/r11_10_mbase_baseline/t80_ez80.vhd.txt').read_bytes()
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();s=s.replace('        Extension_State : out std_logic;', '        MBASE_State : out std_logic_vector(7 downto 0);\n        Extension_State : out std_logic;');s=s.replace('    signal Upper : upper_array;', '    signal MBASE : std_logic_vector(7 downto 0);\n    signal Upper : upper_array;');s=s.replace('    A_BANK <= Address_Bank_Reg;', '    A_BANK <= Address_Bank_Reg;\n    MBASE_State <= MBASE;');s=s.replace("Address_Bank_Reg<=x\"00\"; Index_Bank<=x\"00\";", "Address_Bank_Reg<=x\"00\"; Index_Bank<=x\"00\";MBASE<=x\"00\";",1)
s=s.replace('''            elsif T_Res='1' then
                Address_Bank_Reg<=x"00";''','''            elsif T_Res='1' then
                -- R12: short data and Z80 instruction addresses use MBASE.
                Address_Bank_Reg<=x"00";
                if Extensions_Enabled='1' then Address_Bank_Reg<=MBASE;end if;''',1)
s=s.replace('else PC<=resize(unsigned(RegBusC),24);Address_Bank_Reg<=x"00";ADL_Mode<=\'0\';end if;', 'else PC<=resize(unsigned(RegBusC),24);Address_Bank_Reg<=MBASE;ADL_Mode<=\'0\';end if;',1)
s=s.replace('Address_Reg<=DI_Reg & TmpAddr(7 downto 0);Address_Bank_Reg<=x"00";ADL_Mode<=\'0\';','Address_Reg<=DI_Reg & TmpAddr(7 downto 0);Address_Bank_Reg<=MBASE;ADL_Mode<=\'0\';',1)
s=s.replace("if ADL_Mode='0' then Extensions_Enabled<='0';end if;Unlock_Armed<='0';", "if ADL_Mode='0' then Extensions_Enabled<='0';MBASE<=x\"00\";end if;Unlock_Armed<='0';",1)
# Commit after all legacy ACC updates; neither instruction alters F.
a=s.index('\n        end if;\n\n        end if;\n\n    end process;',s.index('            if TState = 1 and I_BT'))
s=s[:a]+'''\n            -- LD MB,A / LD A,MB are ADL-only; Z80 mode is a NOP.
            if Extensions_Enabled='1' and ADL_Mode='1' and ISet="10" and
                MCycle="001" and TState=4 and IntCycle='0' and NMICycle='0' then
                if IR=x"6D" then MBASE<=ACC;
                elsif IR=x"6E" then ACC<=MBASE;end if;
            end if;
'''+s[a:];p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_pack_ez80.vhd';s=p.read_text().replace('        Extension_State : out std_logic;', '        MBASE_State : out std_logic_vector(7 downto 0);\n        Extension_State : out std_logic;');p.write_text(s)
p=r/'fpga/G80A_eZ80/g80a_ez80.vhd';s=p.read_text().replace('    signal Extension_State_i : std_logic;', '    signal Extension_State_i : std_logic;\n    signal MBASE_i : std_logic_vector(7 downto 0);');s=s.replace('Extension_State=>Extension_State_i,','Extension_State=>Extension_State_i, MBASE_State=>MBASE_i,');s=s.replace('when x"C4"=>Diag_Read<=x"87";','when x"C4"=>Diag_Read<=x"97";').replace('when x"C6"=>Diag_Read<=x"78";','when x"C6"=>Diag_Read<=x"68";').replace('when x"C8"|x"C9"=>Diag_Read<=x"00";','when x"C8"=>Diag_Read<=MBASE_i;\n            when x"C9"=>Diag_Read<=x"00";');s=s.replace('process(Diag_Select, Extension_State_i)','process(Diag_Select, Extension_State_i, MBASE_i)');p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();a=s.index('                -- Mode-bearing RETI.L/RETN.L');s=s[:a]+'''                -- R12: replace undocumented ED aliases while extensions are enabled.
                -- Actual transfer is ADL-only and preserves all flags.
                if Ext_Active='1' and Mode=0 and ISet="10" and (IR=x"6D" or IR=x"6E") and IntCycle='0' and NMICycle='0' then
                    MCycles<="001";TStates<="101";NoRead<='1';Read_To_Reg<='0';Read_To_Acc<='0';Save_ALU<='0';
                    Inc_PC<='0';Inc_WZ<='0';IncDec_16<="0000";Set_Addr_To<=aNone;LDZ<='0';LDW<='0';
                    Jump<='0';JumpXY<='0';Call<='0';RstP<='0';I_RETN<='0';IMode<="11";
                    SetDI<='0';SetEI<='0';Halt<='0';Special_LD<="000";Arith16<='0';
                end if;
'''+s[a:];p.write_text(s)
