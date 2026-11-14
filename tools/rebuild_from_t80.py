from pathlib import Path
import re,hashlib,json
r=Path(__file__).resolve().parent.parent
src=r/'fpga/G80A';dst=r/'fpga/G80A_eZ80';dst.mkdir(exist_ok=True)
texts={n:(src/(n+'.vhd')).read_text() for n in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a')}
for n,s in texts.items():
 for old,new in [('T80_Pack','T80_eZ80_Pack'),('T80_MCode','T80_MCode_eZ80'),('T80_ALU','T80_ALU_eZ80'),('T80_Reg','T80_Reg_eZ80'),('T80','T80_eZ80'),('G80a','G80A_eZ80')]:
  s=re.sub(r'\b'+old+r'\b',new,s,flags=re.I)
 texts[n]=s
# Keep declaration/instantiation interfaces aligned.
for n in ('t80_pack','t80','g80a'):
 s=texts[n]
 # Only CPU and wrapper have the IOWait generic.
 s=re.sub(r'(IOWait\s*: integer := [01])',r'DATA_EXTENDED : boolean := true;\n        \1',s)
 # Add bank/status to the core declaration only, after its 16-bit address.
 s=re.sub(r'(A\s*: out std_logic_vector\(15 downto 0\);)',r'\1\n        A_BANK : out std_logic_vector(7 downto 0);\n        Extension_State : out std_logic;',s)
 texts[n]=s
# Mcode has additional state inputs.
for n in ('t80_pack','t80_mcode'):
 s=texts[n].replace('IR          : in std_logic_vector(7 downto 0);','IR          : in std_logic_vector(7 downto 0);')
 s=re.sub(r'(IR\s*: in std_logic_vector\(7 downto 0\);)',r'\1\n                Ext_Active, Data_Long, Stream_Long : in std_logic;',s)
 texts[n]=s
s=texts['t80_mcode'].replace('process (IR, ISet, MCycle, F, NMICycle, IntCycle, XY_State)','process (IR, ISet, MCycle, F, NMICycle, IntCycle, XY_State, Ext_Active, Data_Long, Stream_Long)')
insert='''
                -- R1 only: explicit suffixes, immediate register loads, byte data access.
                if Ext_Active='1' and Mode=0 and IntCycle='0' and NMICycle='0' then
                    if ISet="00" and (IR=x"40" or IR=x"49" or IR=x"52" or IR=x"5B") then
                        Prefix<="11";
                    end if;
                    if ISet="00" and IR(7 downto 6)="00" and IR(3 downto 0)="0001" and Stream_Long='1' then
                        MCycles<="100";
                        if MCycle="100" then Inc_PC<='1'; Read_To_Reg<='0'; end if;
                    end if;
                    -- Readback of the separate SPL, into bank-00 diagnostic memory.
                    -- Only LD.LIS (nn),SP (49 ED 73 nn nn) is in the R1 subset.
                    if ISet="10" and IR=x"73" and Data_Long='1' and Stream_Long='0' then
                        MCycles<="110";
                        if MCycle="101" then
                            Inc_WZ<='1'; Set_Addr_To<=aZI; Set_BusB_To<="1110";
                        elsif MCycle="110" then
                            Inc_PC<='0'; Set_Addr_To<=aNone; NoRead<='0'; Write<='1';
                        end if;
                    end if;
                end if;
'''
s=s.replace('        end process;',insert+'\n        end process;');texts['t80_mcode']=s
s=texts['t80']
s=s.replace('    -- Registers','''    -- R1: PC and SPS stay 16-bit. No ADL execution/interrupts in this stage.
    type upper_array is array(0 to 7) of std_logic_vector(7 downto 0);
    signal Upper : upper_array;
    signal SPL : unsigned(23 downto 0);
    signal Extensions_Enabled, Unlock_Armed : std_logic;
    signal Width_Pending, Data_Long, Stream_Long : std_logic;
    signal Width_Code : std_logic_vector(7 downto 0);
    signal Index_Bank : std_logic_vector(7 downto 0);
    signal SP_Readback : std_logic;
    signal Load_Upper_Index : std_logic_vector(2 downto 0);
    -- Registers''',1)
s=s.replace('            IR => IR,','            IR => IR,\n            Ext_Active=>Extensions_Enabled, Data_Long=>Data_Long, Stream_Long=>Stream_Long,',1)
s=s.replace("    ClkEn <=",'''    Load_Upper_Index<=XY_State(1) & "11" when IR(5 downto 4)="10" and XY_State/="00" else Alternate & IR(5 downto 4);
    Extension_State<=Extensions_Enabled;
    SP_Readback<='1' when ISet="10" and IR=x"73" and Data_Long='1' and Stream_Long='0' else '0';
    ClkEn <=''')
s=s.replace("            PC <= (others => '0');",'''            Upper <= (others=>(others=>'0')); SPL <= (others=>'1');
            Extensions_Enabled<='0'; Unlock_Armed<='0';
            Width_Pending<='0'; Width_Code<=x"40"; Data_Long<='0'; Stream_Long<='0';
            A_BANK<=x"00"; Index_Bank<=x"00";
            PC <= (others => '0');''',1)
# bank is registered together with address; never suffix-bank instruction fetch/I/O/IRQ.
s=s.replace("            MCycles <= MCycles_d;",'''            MCycles <= MCycles_d;
            if MCycle="001" and TState=2 and Wait_n='1' then A_BANK<=x"00";
            elsif T_Res='1' then
                A_BANK<=x"00";
                if Extensions_Enabled='1' and Data_Long='1' and IntCycle='0' and NMICycle='0' and IORQ_i='0' then
                    if Set_Addr_To=aBC or Set_Addr_To=aDE then
                        A_BANK<=Upper(to_integer(unsigned(RegAddrC)));
                    elsif Set_Addr_To=aXY then
                        if XY_State="00" then A_BANK<=Upper(to_integer(unsigned(RegAddrC)));
                        elsif NextIs_XY_Fetch='0' then A_BANK<=Index_Bank;end if;
                    end if;
                end if;
            end if;
            -- Explicit local gate, not a Zilog architectural register.
            if T_Res='1' and IORQ_i='1' and Write='1' then
                if DATA_EXTENDED and A=x"E7E7" then
                    if DO=x"00" then Extensions_Enabled<='0'; Unlock_Armed<='0';
                    elsif DO=x"A5" then Unlock_Armed<='1';
                    elsif DO=x"5A" and Unlock_Armed='1' then Extensions_Enabled<='1';Unlock_Armed<='0';
                    else Unlock_Armed<='0';end if;
                else Unlock_Armed<='0';end if;
            end if;''',1)
needle="                    if IntCycle = '1' and IStatus = \"01\" then"
s=s.replace(needle,'''                    if Extensions_Enabled='1' and IntCycle='0' and NMICycle='0' and Halt_FF='0' then
                        if ISet="00" and (DInst=x"40" or DInst=x"49" or DInst=x"52" or DInst=x"5B") then
                            Width_Pending<='1'; Width_Code<=DInst;
                            Data_Long<='0';Stream_Long<='0';
                        elsif DInst/=x"DD" and DInst/=x"FD" and DInst/=x"ED" and DInst/=x"CB" then
                            Data_Long<=Width_Pending and Width_Code(3);
                            Stream_Long<=Width_Pending and Width_Code(4);
                            Width_Pending<='0';
                        end if;
                    else Width_Pending<='0';Data_Long<='0';Stream_Long<='0';end if;
'''+needle,1)
s=s.replace("                            if IR(5) = '1' then",'''                            if Extensions_Enabled='1' and (IR=x"40" or IR=x"49" or IR=x"52" or IR=x"5B") then null;
                            elsif IR(5) = '1' then''',1)
# The third byte is consumed independently from data width; .LIS zero extends.
s=s.replace("            if TState = 3 then",'''            if TState=3 and IntCycle='0' and NMICycle='0' and Extensions_Enabled='1' and ISet="00" and IR(7 downto 6)="00" and IR(3 downto 0)="0001" then
                if MCycle="011" and Stream_Long='0' and Data_Long='1' then
                    if IR(5 downto 4)="11" then SPL(23 downto 16)<=(others=>'0');
                    else Upper(to_integer(unsigned(Load_Upper_Index)))<=x"00";end if;
                elsif MCycle="100" and Stream_Long='1' then
                    if IR(5 downto 4)="11" then
                        if Data_Long='1' then SPL(23 downto 16)<=unsigned(DI_Reg);end if;
                    else
                        if Data_Long='1' then Upper(to_integer(unsigned(Load_Upper_Index)))<=DI_Reg;
                        else Upper(to_integer(unsigned(Load_Upper_Index)))<=x"00";end if;
                    end if;
                end if;
            end if;
            if TState = 3 then''',1)
s=s.replace("                    SP(7 downto 0) <= unsigned(Save_Mux);",'''                    if Data_Long='1' and ISet="00" and IR=x"31" then SPL(7 downto 0)<=unsigned(Save_Mux);
                    else SP(7 downto 0)<=unsigned(Save_Mux);end if;''')
s=s.replace("                    SP(15 downto 8) <= unsigned(Save_Mux);",'''                    if Data_Long='1' and ISet="00" and IR=x"31" then SPL(15 downto 8)<=unsigned(Save_Mux);
                    else SP(15 downto 8)<=unsigned(Save_Mux);end if;''')
# Indexed data addresses must carry/borrow into the upper byte.
s=s.replace('    signal SP_Readback : std_logic;','    signal SP_Readback : std_logic;\n    signal Indexed_Address : signed(23 downto 0);')
s=s.replace('    Extension_State<=','    Indexed_Address<=(signed(Upper(to_integer(unsigned(RegAddrC)))) & signed(RegBusC))+resize(signed(DI_Reg),24);\n    Extension_State<=')
s=s.replace('if MCycle = "110" then','if MCycle = "110" and SP_Readback=\'0\' then',1)
s=s.replace('if TState = 3 and MCycle = "110" then','if TState = 3 and MCycle = "110" and SP_Readback=\'0\' then',1)
s=s.replace('TmpAddr <= std_logic_vector(signed(RegBusC) + signed(DI_Reg));','''TmpAddr <= std_logic_vector(signed(RegBusC) + signed(DI_Reg));
                    if Data_Long='1' then
                        TmpAddr<=std_logic_vector(Indexed_Address(15 downto 0));
                        Index_Bank<=std_logic_vector(Indexed_Address(23 downto 16));
                    end if;''')
s=s.replace('BusB <= std_logic_vector(SP(7 downto 0));',"if SP_Readback='1' then BusB<=std_logic_vector(SPL(7 downto 0));else BusB <= std_logic_vector(SP(7 downto 0));end if;")
s=s.replace('BusB <= std_logic_vector(SP(15 downto 8));',"if SP_Readback='1' then BusB<=std_logic_vector(SPL(15 downto 8));else BusB <= std_logic_vector(SP(15 downto 8));end if;")
s=s.replace('BusB <= "00000000";',"if SP_Readback='1' then BusB<=std_logic_vector(SPL(23 downto 16));else BusB <= \"00000000\";end if;")
# Delay interrupts through the prefix chain. Actual IRQ remains original Z80-only.
s=s.replace('and Prefix = "00" then','and Prefix = "00" and Width_Pending=\'0\' then')
s=s.replace('and Prefix = "00" and SetEI',"and Prefix = \"00\" and Width_Pending='0' and SetEI")
s=s.replace("A <= std_logic_vector(unsigned(TmpAddr) + 1);","if SP_Readback='1' and MCycle=\"101\" then A<=std_logic_vector(unsigned(A)+1);else A <= std_logic_vector(unsigned(TmpAddr) + 1);end if;")
texts['t80']=s
s=texts['g80a']
s=s.replace('    signal CEN',"    signal Bank_i : std_logic_vector(7 downto 0);\n    signal Extension_State_i : std_logic;\n    signal CEN",1)
# Wrapper interface has A24, not A_BANK/status ports (added only to 16-bit CPU A).
s=s.replace('        A_BANK : out std_logic_vector(7 downto 0);\n        Extension_State : out std_logic;','        A24 : out std_logic_vector(23 downto 0);')
s=s.replace('    A <= A_i',"    A24<=Bank_i & A_i when BUSAK_n_i='1' else (others=>'Z');\n    A <= A_i",1)
s=s.replace('            Mode => Mode,','            DATA_EXTENDED=>DATA_EXTENDED,\n            Mode => Mode,',1)
s=s.replace('            A => A_i,','            A => A_i, A_BANK=>Bank_i, Extension_State=>Extension_State_i,',1)
s=s.replace('DI_Reg <= to_x01(DI);',"if A_i=x\"E7E7\" and IORQ='1' and Write='0' then DI_Reg<=\"1110000\" & Extension_State_i;\n                    else DI_Reg <= to_x01(DI);end if;")
texts['g80a']=s
for n,s in texts.items(): (dst/(n+'_ez80.vhd')).write_text(s)
(r/'doc/provenance.json').write_text(json.dumps({n:hashlib.sha256((src/(n+'.vhd')).read_bytes()).hexdigest() for n in texts},indent=2)+'\n')
