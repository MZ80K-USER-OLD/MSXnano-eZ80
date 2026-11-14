"""P2 diagnostic service in existing wrapper; inactive until explicit D8."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent;p=r/'fpga/G80A_eZ80/g80a_ez80.vhd';s=p.read_text()
s=s.replace('        DATA_EXTENDED : boolean := true;', '        DATA_EXTENDED : boolean := true;\n        DIAGNOSTICS : boolean := false;',1)
s=s.replace('    signal Bank_i :', '''    signal Diag_Select : std_logic_vector(7 downto 0);
    signal Diag_Read : std_logic_vector(7 downto 0);
    signal Diag_Active, Diag_IRQ, Diag_NMI_Arm, HALT_i : std_logic;
    signal Diag_NMI_Count : unsigned(3 downto 0);
    signal INT_Input_n, NMI_Input_n, Vector_Window : std_logic;
    signal Bank_i :''',1)
s=s.replace("    A24<=Bank_i & A_i when BUSAK_n_i='1' else (others=>'Z');", """    -- Decode read intent before MREQ/T1, so the existing bridge can assert
    -- WAIT before RD. Captured SDRAM requests remain untouched downstream.
    Vector_Window <= '1' when DIAGNOSTICS and Diag_Active='1' and Bank_i=x"00" and A_i(15 downto 7)="000000000" and
        Write='0' and IORQ='0' and IntCycle_n='1' and RFSH_n_i='1' else '0';
    A24 <= x"0F" & A_i when Vector_Window='1' and BUSAK_n_i='1' else
           Bank_i & A_i when BUSAK_n_i='1' else (others=>'Z');
    HALT_n<=HALT_i;
    INT_Input_n <= not Diag_IRQ when DIAGNOSTICS and Diag_Active='1' else INT_n;
    NMI_Input_n <= '0' when DIAGNOSTICS and Diag_NMI_Count/=0 else NMI_n;
    process(Diag_Select, Extension_State_i)
    begin
        Diag_Read<="1110000" & Extension_State_i;
        if Extension_State_i='1' then
            case Diag_Select is
            when x"C0"=>Diag_Read<=x"45";
            when x"C1"=>Diag_Read<=x"5A";
            when x"C2"=>Diag_Read<=x"02";
            when x"C3"=>Diag_Read<=x"A7";
            when x"C4"=>Diag_Read<=x"87";
            when x"C5"=>if DIAGNOSTICS then Diag_Read<=x"82";else Diag_Read<=x"02";end if;
            when x"C6"=>Diag_Read<=x"78";
            when x"C7"=>if DIAGNOSTICS then Diag_Read<=x"7D";else Diag_Read<=x"FD";end if;
            when x"C8"|x"C9"=>Diag_Read<=x"00";
            when others=>null;
            end case;
        end if;
    end process;
    process(RESET_n, CLK_n)
    begin
        if RESET_n='0' then
            Diag_Select<=x"FF";Diag_Active<='0';Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
        elsif rising_edge(CLK_n) then
            if clk_enable='1' then
                if Diag_NMI_Count/=0 then Diag_NMI_Count<=Diag_NMI_Count-1;end if;
                if DIAGNOSTICS and Diag_Active='1' and Diag_NMI_Arm='1' and HALT_i='0' then
                    Diag_NMI_Count<=to_unsigned(8,4);Diag_NMI_Arm<='0';
                end if;
                if Extension_State_i='0' then
                    Diag_Select<=x"FF";Diag_Active<='0';Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
                end if;
                if IORQ='1' and Write='1' and A_i=x"E7E7" and TState="011" then
                    if DO=x"A5" or DO=x"5A" or DO=x"00" then Diag_Select<=x"FF";
                    elsif Extension_State_i='1' then
                        if DO(7 downto 4)=x"C" then Diag_Select<=DO;
                        elsif DIAGNOSTICS then
                            case DO is
                            when x"D8"=>Diag_Active<='1';Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
                            when x"D1"=>if Diag_Active='1' then Diag_IRQ<='1';end if;
                            when x"D2"=>if Diag_Active='1' then Diag_NMI_Arm<='1';end if;
                            when x"D4"=>Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
                            when x"D0"=>Diag_Active<='0';Diag_IRQ<='0';Diag_NMI_Arm<='0';Diag_NMI_Count<=(others=>'0');
                            when others=>null;
                            end case;
                        end if;
                    end if;
                end if;
            end if;
        end if;
    end process;""",1)
s=s.replace('            HALT_n => HALT_n,', '            HALT_n => HALT_i,',1).replace('            INT_n => INT_n,', '            INT_n => INT_Input_n,',1).replace('            NMI_n => NMI_n,', '            NMI_n => NMI_Input_n,',1)
s=s.replace('then DI_Reg<="1110000" & Extension_State_i;', "and IntCycle_n='1' then DI_Reg<=Diag_Read;\n                    elsif DIAGNOSTICS and Diag_Active='1' and IntCycle_n='0' and MCycle=\"001\" then DI_Reg<=x\"FE\";",1)
p.write_text(s)
p=r/'fpga/top_ez80.v';s=p.read_text().replace('.DATA_EXTENDED (EZ80_EXTENDED),', '.DIAGNOSTICS (EZ80_EXTENDED), // P2 service, inactive until explicit D8\n        .DATA_EXTENDED (EZ80_EXTENDED),',1);p.write_text(s)
