"""Apply the V34.1 boot guard to an unmodified V34 source tree, once."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
folder=r/'fpga/G80A_eZ80'
for name in ('t80_pack_ez80.vhd','t80_ez80.vhd','g80a_ez80.vhd'):
 p=folder/name;s=p.read_text();assert 'BOOT_Z80_COMPAT' not in s
 s=s.replace('FETCH24     : boolean := false;', 'FETCH24     : boolean := false;\n        BOOT_Z80_COMPAT : boolean := false;',1)
 if name!='g80a_ez80.vhd':
  s=s.replace('A_BANK      : out std_logic_vector(7 downto 0) := x"00";', 'A_BANK      : out std_logic_vector(7 downto 0) := x"00";\n        EXT_ACTIVE : out std_logic := \'1\';',1)
 if name=='t80_pack_ez80.vhd':
  s=s.replace('Data_Long   : in std_logic;', "ISA_Active : in std_logic := '1';\n        Data_Long   : in std_logic;",1)
 if name=='g80a_ez80.vhd':
  s=s.replace('    signal CEN          : std_logic;', '    signal Extension_State : std_logic;\n    signal CEN          : std_logic;',1)
  s=s.replace('and ENABLE_EZ80_ISA else', "and ENABLE_EZ80_ISA and Extension_State='1' else",1)
  s=s.replace('FETCH24 => FETCH24,', 'FETCH24 => FETCH24, BOOT_Z80_COMPAT=>BOOT_Z80_COMPAT,',1)
  s=s.replace('A_BANK => A_bank_i,','A_BANK => A_bank_i, EXT_ACTIVE=>Extension_State,',1)
  s=s.replace('DI_Reg <= to_x01(DI);', '''if BOOT_Z80_COMPAT and A_i=x"E7E7" and IORQ_n_i='0' and RD_n_i='0' and IntCycle_n='1' then
                        DI_Reg<=x"E" & "000" & Extension_State;
                    else DI_Reg <= to_x01(DI);end if;''',1)
 if name=='t80_ez80.vhd':
  s=s.replace('    signal ADL_State : std_logic;', '''    signal ADL_State : std_logic;
    signal Extensions_Enabled, Unlock_Armed : std_logic;''',1)
  s=s.replace('begin\n\n    mcode', "begin\n    EXT_ACTIVE<=Extensions_Enabled;\n\n    mcode",1)
  s=s.replace('Data_Long => Immediate_Long,', 'ISA_Active=>Extensions_Enabled, Data_Long => Immediate_Long,',1)
  s=s.replace("elsif T_Res='1' then\n                    A_BANK<=MBASE;", "elsif Extensions_Enabled='0' then A_BANK<=x\"00\";\n                elsif T_Res='1' then\n                    A_BANK<=MBASE;",1)
  s=s.replace("Fetch_Long <= FETCH24 and (not ENABLE_MIXED or ADL_State='1');", "Fetch_Long <= FETCH24 and Extensions_Enabled='1' and (not ENABLE_MIXED or ADL_State='1');")
  s=s.replace("Immediate_Long <= Width_Stream_Long when", "Immediate_Long <= '0' when Extensions_Enabled='0' else Width_Stream_Long when")
  s=s.replace("when FETCH24 and Data_Long='1'", "when FETCH24 and Extensions_Enabled='1' and Data_Long='1'")
  s=s.replace("            MBASE<=x\"00\";", '''            MBASE<=x"00";
            if BOOT_Z80_COMPAT then Extensions_Enabled<='0';else Extensions_Enabled<='1';end if;
            Unlock_Armed<='0';''',1)
  s=s.replace("if IntCycle = '0' and NMICycle = '0' and Halt_FF = '0' then", "if Extensions_Enabled='1' and IntCycle = '0' and NMICycle = '0' and Halt_FF = '0' then",1)
  s=s.replace("if ENABLE_SUFFIX_V2 and FETCH24 and ENABLE_MIXED and Mode=0", "if Extensions_Enabled='1' and ENABLE_SUFFIX_V2 and FETCH24 and ENABLE_MIXED and Mode=0",1)
  s=s.replace("if ENABLE_EZ80_ISA and Mode=0", "if Extensions_Enabled='1' and ENABLE_EZ80_ISA and Mode=0")
  marker='''
        end if;

        end if;

    end process;

---------------------------------------------------------------------------'''
  assert s.count(marker)==1
  logic='''
            -- Local MSXnano control port, full 16-bit decode. No ISA opcode added.
            -- A5 then 5A unlocks; 00 locks. Only Z80/MBASE00/bank00 may change it.
            if BOOT_Z80_COMPAT and T_Res='1' and IORQ_i='1' and Write='1' then
                Unlock_Armed<='0';
                if A=x"E7E7" and ADL_State='0' and MBASE=x"00" and PC(23 downto 16)=x"00" then
                    if DO=x"00" then Extensions_Enabled<='0';
                    elsif DO=x"A5" then Unlock_Armed<='1';
                    elsif DO=x"5A" and Unlock_Armed='1' then Extensions_Enabled<='1';end if;
                end if;
            end if;
            if Extensions_Enabled='0' then
                Data_Long<='0';Long_Pending<='0';Short_Pending<='0';Short_Instruction<='0';
                Store_Pending<='0';Store_Long<='0';Width_Pending<='0';Width_Load_Active<='0';
                Width_Stream_Long<='0';Width_Explicit<='0';Frame_Enabled<='0';Frame_Last<='0';
                if Extensions_Enabled='0' then ADL_State<='0';MBASE<=x"00";end if;
            end if;
'''
  s=s.replace(marker,logic+marker,1)
 p.write_text(s)
p=folder/'t80_mcode_ez80.vhd';s=p.read_text()
s=s.replace('Data_Long   : in std_logic;', "ISA_Active : in std_logic := '1';\n                Data_Long   : in std_logic;",1)
s=s.replace('process (Width_Explicit,', 'process (ISA_Active, Width_Explicit,',1)
s=s.replace("ENABLE_EZ80_ISA and Mode=0", "ENABLE_EZ80_ISA and ISA_Active='1' and Mode=0",1);p.write_text(s)
p=r/'fpga/top_ez80.v';s=p.read_text().replace('.FETCH24 (EZ80_EXTENDED),','.FETCH24 (EZ80_EXTENDED),\n        .BOOT_Z80_COMPAT (EZ80_EXTENDED),',1)
s=s.replace('// v34: extension profile enabled, Z80 reset entry; ADL tests remain DI-only.', '// v34.1: hardware extensions present; CPU locks them off for Z80-compatible boot.')
p.write_text(s)
print('Applied boot guard to core/wrapper/decoder and board generic')
