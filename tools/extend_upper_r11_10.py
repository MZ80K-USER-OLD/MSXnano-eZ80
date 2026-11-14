from pathlib import Path
import re
r=Path(__file__).resolve().parent.parent;p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text()
s=s.replace('    signal Upper : upper_array;','''    signal Upper : upper_array;
    signal Upper_Port_Events : std_logic_vector(7 downto 0);
    signal Upper_Port_WE : std_logic;
    signal Upper_Port_Index : std_logic_vector(2 downto 0);
    signal Upper_Port_Data, Upper_Inc_Byte, Upper_Immediate_Byte : std_logic_vector(7 downto 0);
    function Upper_Mask(v : std_logic_vector; en : std_logic) return std_logic_vector is
        variable result : std_logic_vector(v'range);
    begin
        result:=(others=>'0');if en='1' then result:=v;end if;return result;
    end function;
''',1)
a=s.index('    process (RESET_n, CLK_n)');b=s.index('\n---------------------------------------------------------------------------',a);body=s[a:b]
body=body.replace("Upper <= (others=>(others=>'0')); SPL",'SPL',1)
body,n=re.subn(r'Upper\([^;]*?\)\s*<=.*?;','null;',body,flags=re.S);assert n==13,n
s=s[:a]+body+s[b:]
a=s.index('    process (RESET_n, CLK_n)')
new='''    -- R11.10: ordinary upper-byte commits share one combinational write port.
    -- These eight events belong to disjoint opcode families. No pipeline
    -- stage is added: the original enabled rising edge performs the commit.
    Upper_Port_Events(0)<='1' when Pair_Absolute='1' and Pair_Read='1' and Data_Long='1' and Pair_SP='0' and
        TState=3 and to_integer(unsigned(MCycle))=Pair_Address_Last+3 else '0';
    Upper_Port_Events(1)<=LEA_Commit and Data_Long;
    Upper_Port_Events(2)<=Arith_Commit;
    Upper_Port_Events(3)<=EX_SP_Result_WE;
    Upper_Port_Events(4)<='1' when Block_Long='1' and IncDec_16(2)='1' and
        ((MCycle="001" and TState=3) or (MCycle/="001" and TState=2 and Wait_n='1')) else '0';
    Upper_Port_Events(5)<='1' when Wide_IncDec='1' and MCycle="001" and TState=3 and IR(5 downto 4)/="11" and
        ((IncDec_16(3)='1' and RegBusA=x"0000") or (IncDec_16(3)='0' and RegBusA=x"FFFF")) else '0';
    Upper_Port_Events(6)<='1' when Wide_Stack='1' and IR(3 downto 0)="0001" and MCycle="100" and TState=3 and IR(5 downto 4)/="11" else '0';
    Upper_Port_Events(7)<='1' when TState=3 and IntCycle='0' and NMICycle='0' and Extensions_Enabled='1' and
        ISet="00" and IR(7 downto 6)="00" and IR(3 downto 0)="0001" and IR(5 downto 4)/="11" and
        ((MCycle="011" and Stream_Long='0' and Data_Long='1') or (MCycle="100" and Stream_Long='1')) else '0';
    Upper_Port_WE<='1' when Upper_Port_Events/=x"00" else '0';
    Upper_Port_Index<=Upper_Mask(Pair_Upper_Index,Upper_Port_Events(0)) or Upper_Mask(EA_Target,Upper_Port_Events(1)) or
        Upper_Mask(Arith_Target,Upper_Port_Events(2)) or Upper_Mask(EX_SP_Index,Upper_Port_Events(3)) or
        Upper_Mask(RegAddrA,Upper_Port_Events(4)) or Upper_Mask(RegAddrA,Upper_Port_Events(5)) or
        Upper_Mask(Stack_Upper_Index,Upper_Port_Events(6)) or Upper_Mask(Load_Upper_Index,Upper_Port_Events(7));
    Upper_Inc_Byte<=std_logic_vector(unsigned(Upper(to_integer(unsigned(RegAddrA))))-1) when IncDec_16(3)='1'
        else std_logic_vector(unsigned(Upper(to_integer(unsigned(RegAddrA))))+1);
    Upper_Immediate_Byte<=DI_Reg when Stream_Long='1' and Data_Long='1' else x"00";
    Upper_Port_Data<=Upper_Mask(DI_Reg,Upper_Port_Events(0)) or Upper_Mask(EA_Result(23 downto 16),Upper_Port_Events(1)) or
        Upper_Mask(std_logic_vector(Arith_Result(23 downto 16)),Upper_Port_Events(2)) or Upper_Mask(EX_SP_Read(23 downto 16),Upper_Port_Events(3)) or
        Upper_Mask(std_logic_vector(Block_Inc_Result(23 downto 16)),Upper_Port_Events(4)) or Upper_Mask(Upper_Inc_Byte,Upper_Port_Events(5)) or
        Upper_Mask(DI_Reg,Upper_Port_Events(6)) or Upper_Mask(Upper_Immediate_Byte,Upper_Port_Events(7));
    process(RESET_n, CLK_n)
    begin
        if RESET_n='0' then Upper<=(others=>(others=>'0'));
        elsif rising_edge(CLK_n) then
            if ClkEn='1' then
                -- EX DE,HL updates both entries from their old values.
                if Extensions_Enabled='1' and Data_Long='1' and ExchangeDH='1' and TState=3 then
                    Upper(to_integer(unsigned'(Alternate & "10")))<=Upper(to_integer(unsigned'(Alternate & "01")));
                    Upper(to_integer(unsigned'(Alternate & "01")))<=Upper(to_integer(unsigned'(Alternate & "10")));
                end if;
                -- Preserve the original priority relative to the exchange.
                if Upper_Port_WE='1' then Upper(to_integer(unsigned(Upper_Port_Index)))<=Upper_Port_Data;end if;
            end if;
        end if;
    end process;

'''
s=s[:a]+new+s[a:];p.write_text(s)
