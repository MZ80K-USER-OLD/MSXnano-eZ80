from pathlib import Path
r=Path(__file__).resolve().parent.parent;p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text()
s=s.replace('signal EX_SP_Read : std_logic_vector(23 downto 0);','signal EX_SP_Read, EX_SP_Source : std_logic_vector(23 downto 0);')
a=s.index('    process(SPL,MCycle) variable offset:');b=s.index("    Arith_Long<=",a)
s=s[:a]+'''    -- Address work register advances only after an accepted T2.
    -- M1/T3 prepares the first read before the M1/T4 address latch.
'''+s[b:]
s=s.replace("EX_SP_Read<=(others=>'0');", "EX_SP_Read<=(others=>'0');EX_SP_Source<=(others=>'0');EX_SP_Address<=(others=>'0');",1)
needle="            if EX_SP_Long='1' and TState=3 then\n"
insert='''            if EX_SP_Long='1' then
                if MCycle="001" and TState=3 then EX_SP_Address<=SPL;end if;
                if MCycle="001" and TState=4 then
                    EX_SP_Source<=Upper(to_integer(unsigned(EX_SP_Index))) & RegBusA;
                end if;
                if TState=2 and Wait_n='1' then
                    case MCycle is
                    when "010"|"011"|"101"|"110"=>EX_SP_Address<=EX_SP_Address+1;
                    when "100"=>EX_SP_Address<=SPL;
                    when others=>null;
                    end case;
                end if;
            end if;
'''
assert needle in s;s=s.replace(needle,insert+needle,1)
needle='''                if I_RLD = '1' then'''
insert='''                if EX_SP_Long='1' then
                    case MCycle is
                    when "101"=>Data_Out_Reg<=EX_SP_Source(7 downto 0);
                    when "110"=>Data_Out_Reg<=EX_SP_Source(15 downto 8);
                    when "111"=>Data_Out_Reg<=EX_SP_Source(23 downto 16);
                    when others=>null;
                    end case;
                end if;
'''
assert needle in s;s=s.replace(needle,insert+needle,1);p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();a=s.index('-- R4 EX(SPL)');b=s.index('-- R5 long ADD',a);part=s[a:b]
part=part.replace('when "100"=>Set_BusB_To<="0101";','when "100"=>null;').replace('when "101"=>Write<=\'1\';Set_BusB_To<="0100";', 'when "101"=>Write<=\'1\';').replace('when "110"=>Write<=\'1\';Set_BusB_To<="1110";', 'when "110"=>Write<=\'1\';')
s=s[:a]+part+s[b:];p.write_text(s);print('Applied EX(SPL) source/address work registers, same bus-cycle schedule')
