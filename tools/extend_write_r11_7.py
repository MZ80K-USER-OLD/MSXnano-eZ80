from pathlib import Path
import re
r=Path(__file__).resolve().parent.parent
f=r/'fpga/G80A_eZ80/t80_pack_ez80.vhd';s=f.read_text().replace('package T80_eZ80_Pack is','package T80_eZ80_Pack is\n    function Classify_Write(op : std_logic_vector(7 downto 0)) return std_logic_vector;',1)
s=s.replace('        IR          : in std_logic_vector(7 downto 0);','        IR          : in std_logic_vector(7 downto 0);\n        Write_Class : in std_logic_vector(7 downto 0);',1)
s+='''
package body T80_eZ80_Pack is
    -- R11.7: raw opcode classification, captured alongside every IR update.
    -- Low nibble is the unprefixed class; high nibble is the ED class.
    function Classify_Write(op : std_logic_vector(7 downto 0)) return std_logic_vector is
        variable c : std_logic_vector(7 downto 0) := x"00";
    begin
        if op=x"22" then c(3 downto 0):=x"1";
        elsif op=x"2A" then c(3 downto 0):=x"2";
        elsif op=x"32" then c(3 downto 0):=x"3";
        elsif op=x"3A" then c(3 downto 0):=x"4";
        elsif op(7 downto 6)="11" and op(3 downto 0)="0101" then c(3 downto 0):=x"5";
        elsif op(7 downto 6)="11" and op(3 downto 0)="0001" then c(3 downto 0):=x"6";
        elsif op=x"E3" then c(3 downto 0):=x"7";
        elsif op(7 downto 6)="00" and op(3 downto 0)="1001" then c(3 downto 0):=x"8";
        elsif op=x"C3" or (op(7 downto 6)="11" and op(2 downto 0)="010") then c(3 downto 0):=x"9";
        elsif op=x"CD" then c(3 downto 0):=x"A";
        elsif op(7 downto 6)="11" and op(2 downto 0)="100" then c(3 downto 0):=x"B";
        elsif op=x"C9" then c(3 downto 0):=x"C";
        elsif op(7 downto 6)="11" and op(2 downto 0)="000" then c(3 downto 0):=x"D";
        elsif op(7 downto 6)="11" and op(2 downto 0)="111" then c(3 downto 0):=x"E";
        end if;
        if op(7 downto 6)="01" and op(2 downto 0)="011" then
            if op(3)='0' then c(7 downto 4):=x"1";else c(7 downto 4):=x"2";end if;
        elsif op(7 downto 6)="01" and op(2 downto 0)="010" then c(7 downto 4):=x"3";
        elsif op(7 downto 6)="01" and op(3 downto 0)="1100" then c(7 downto 4):=x"4";
        elsif op=x"65" or op=x"66" then c(7 downto 4):=x"6";
        elsif op=x"02" or op=x"03" or op=x"12" or op=x"13" or op=x"22" or op=x"23" or
              op=x"32" or op=x"33" or op=x"54" or op=x"55" then c(7 downto 4):=x"5";
        elsif op=x"5D" or op=x"6D" or op=x"75" or op=x"7D" then c(7 downto 4):=x"7";
        elsif op=x"45" or op=x"4D" then c(7 downto 4):=x"8";
        elsif op=x"C7" or op=x"D7" then c(7 downto 4):=x"9";
        end if;
        return c;
    end function;
end package body;
''';f.write_text(s)
f=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=f.read_text().replace('    signal Opcode_Class :','    signal Write_Class : std_logic_vector(7 downto 0);\n    signal Opcode_Class :',1)
s=s.replace('            IR => IR,','            IR => IR, Write_Class=>Write_Class,',1)
s,n=re.subn(r'Opcode_Class<=Classify_Opcode\(([^)]+)\);',r'Opcode_Class<=Classify_Opcode(\1); Write_Class<=Classify_Write(\1);',s);assert n==5,n
f.write_text(s)
f=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=f.read_text().replace('                IR          : in std_logic_vector(7 downto 0);','                IR          : in std_logic_vector(7 downto 0);\n                Write_Class : in std_logic_vector(7 downto 0);',1)
s=s.replace('architecture rtl of T80_MCode_eZ80 is','architecture rtl of T80_MCode_eZ80 is\n        signal Legacy_Write : std_logic;',1)
a=s.index('                -- R1 only:');first=s[:a];rest=s[a:]
first=re.sub(r'\bWrite\s*<=', 'Legacy_Write <=',first)
rest,n=re.subn(r'\bWrite\s*<=\s*\'[01]\';','null;',rest);assert n>20,n
s=first+rest
p=s.rfind('\nend;');s=s[:p]+'''
    -- The legacy writer is unchanged. Extension overrides select one opcode
    -- class in parallel instead of chaining every instruction's Write mux.
    process(Legacy_Write, Write_Class, ISet, MCycle, Ext_Active, Data_Long,
            Stream_Long, ADL_Mode, Has_Width, IntCycle, NMICycle, Branch_Condition)
        variable w : std_logic;
        variable base_kind, ed_kind : std_logic_vector(3 downto 0);
        variable lastaddr, cycle : integer range 0 to 7;
    begin
        w:=Legacy_Write; base_kind:=Write_Class(3 downto 0);ed_kind:=Write_Class(7 downto 4);
        cycle:=to_integer(unsigned(MCycle));
        if Stream_Long='1' then lastaddr:=4;else lastaddr:=3;end if;
        if Ext_Active='1' and Mode=0 and IntCycle='0' and NMICycle='0' then
            if ISet="00" then
                case base_kind is
                when x"1"|x"2" =>
                    if Data_Long='1' or Stream_Long='1' then
                        w:='0';if base_kind=x"1" and cycle>lastaddr then w:='1';end if;
                    end if;
                when x"3"|x"4" =>
                    if Data_Long='1' or Stream_Long='1' then
                        w:='0';if base_kind=x"3" and cycle=lastaddr+1 then w:='1';end if;
                    end if;
                when x"5"|x"6" =>
                    if Data_Long='1' then
                        w:='0';if base_kind=x"5" and cycle>=2 and cycle<=4 then w:='1';end if;
                    end if;
                when x"7" =>
                    if Data_Long='1' then w:='0';if cycle>=5 then w:='1';end if;end if;
                when x"8" => if Data_Long='1' then w:='0';end if;
                when others=>null;
                end case;
            elsif ISet="10" then
                case ed_kind is
                when x"1"|x"2" =>
                    if Data_Long='1' or Stream_Long='1' then
                        w:='0';if ed_kind=x"1" and cycle>lastaddr then w:='1';end if;
                    end if;
                when x"3" => if Data_Long='1' then w:='0';end if;
                when x"4"|x"5" => w:='0';
                when x"6" => w:='0';if cycle>=3 then w:='1';end if;
                when others=>null;
                end case;
            end if;
        end if;
        -- Preserve the original guards, including profiles with Mode/=0,
        -- a closed extension gate, or an interrupt coincident with a suffix.
        if Ext_Active='1' and ISet="00" and IntCycle='0' and NMICycle='0' then
            if base_kind=x"9" and Data_Long=Stream_Long then w:='0';end if;
            if ADL_Mode='1' and Has_Width='0' then
                case base_kind is
                when x"A"|x"B" =>
                    w:='0';if cycle>=5 and (base_kind=x"A" or Branch_Condition='1') then w:='1';end if;
                when x"C"|x"D" => w:='0';
                when x"E" => w:='0';if cycle>=2 then w:='1';end if;
                when others=>null;
                end case;
            end if;
        end if;
        if ADL_Mode='1' and ISet="10" and ed_kind=x"7" then w:='0';end if;
        if Ext_Active='1' and Has_Width='1' and ISet="00" and
           (base_kind=x"A" or base_kind=x"B" or base_kind=x"C" or base_kind=x"D" or base_kind=x"E") then w:='0';end if;
        if Ext_Active='1' and ADL_Mode='1' and (IntCycle='1' or NMICycle='1') then
            w:='0';if cycle>=2 and cycle<=4 then w:='1';end if;
        end if;
        if Ext_Active='1' and ISet="10" and IntCycle='0' and NMICycle='0' then
            if ed_kind=x"9" or (ed_kind=x"8" and (ADL_Mode='1' or Has_Width='1')) then w:='0';end if;
        end if;
        Write<=w;
    end process;
''' + s[p:];f.write_text(s)
