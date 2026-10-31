library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_locked_r1 is
 generic(EXTENSIONS:boolean:=true;INSERT_WAIT:boolean:=false; SEED:boolean:=false;CARRY_IN:boolean:=false);
end;
architecture test of tb_locked_r1 is
 signal clk:std_logic:='0';signal reset_n:std_logic:='0';signal wait_n:std_logic:='1';
 signal phase:natural range 0 to 15:=0;signal ce,cf:std_logic;
 signal a,b:std_logic_vector(15 downto 0);signal di,doa,dob:std_logic_vector(7 downto 0);
 signal ca,cb:std_logic_vector(7 downto 0);
 type bytes_t is array(natural range <>) of std_logic_vector(7 downto 0);
 function makecode return bytes_t is variable m:bytes_t(0 to 255):=(others=>x"76");variable n:natural:=0;
 procedure seq(v:bytes_t) is begin for i in v'range loop m(n):=v(i);n:=n+1;end loop;end;
 procedure put(x:natural) is begin m(n):=std_logic_vector(to_unsigned(x,8));n:=n+1;end;
 begin
 seq((x"31",x"00",x"F0",x"3E",x"19"));
 -- All four bytes retain ordinary Z80 semantics while locked, even before LD rr.
 for pref in 0 to 3 loop
 case pref is when 0=>put(16#40#);when 1=>put(16#49#);when 2=>put(16#52#);when others=>put(16#5B#);end case;
 seq((x"21",x"34",x"12",x"3C",x"22",x"00",x"90"));
 end loop;
 -- Wrong high port and an unarmed 5A must not enable extensions.
 seq((x"01",x"E7",x"E6",x"3E",x"A5",x"ED",x"79",x"3E",x"5A",x"ED",x"79"));
 seq((x"01",x"E7",x"E7",x"ED",x"79",x"ED",x"78"));
 seq((x"52",x"21",x"78",x"56",x"3C",x"22",x"02",x"90"));
 -- A correct first key followed by another I/O write cancels the arm.
 seq((x"3E",x"A5",x"ED",x"79",x"01",x"99",x"00",x"ED",x"79",x"01",x"E7",x"E7",x"3E",x"5A",x"ED",x"79"));
 seq((x"5B",x"DD",x"21",x"BC",x"9A",x"3C",x"DD",x"22",x"04",x"90"));
 seq((x"3E",x"A5",x"ED",x"79",x"49",x"FD",x"21",x"F0",x"DE",x"3C",x"FD",x"22",x"06",x"90"));
 seq((x"AF",x"ED",x"79"));
 -- Native Z80 stack, EX (SP),HL, undocumented NEG/RETN aliases remain legacy.
 seq((x"21",x"44",x"33",x"E5",x"21",x"66",x"55",x"E3",x"E1",x"22",x"08",x"90"));
 if SEED then seq((x"3E",x"81"));else seq((x"3E",x"00"));end if;
 if CARRY_IN then put(16#37#);end if;
 seq((x"ED",x"7C",x"F5",x"C1",x"ED",x"43",x"0A",x"90",x"76"));
 return m;end;
 constant code:bytes_t:=makecode;
 type memory_t is array(0 to 65535) of std_logic_vector(7 downto 0);
 function initial_memory return memory_t is variable m:memory_t:=(others=>x"00");begin m(0):=x"C3";m(1):=x"00";m(2):=x"01";for i in 1 to 7 loop m(i*8):=x"C9";end loop;for i in code'range loop m(256+i):=code(i);end loop;return m;end;
 signal mem:memory_t:=initial_memory;
 begin
 clk<=not clk after 5 ns;reset_n<='1' after 100 ns;
 process(clk) begin if rising_edge(clk) then if reset_n='0' then phase<=0;else phase<=(phase+1) mod 16;end if;end if;end process;
 ce<='1' when phase=0 else '0';cf<='1' when phase=8 else '0';
 original:entity work.G80a port map(RESET_n=>reset_n,CLK_n=>clk,clk_enable=>ce,clk_falling=>cf,WAIT_n=>wait_n,INT_n=>'1',NMI_n=>'1',BUSRQ_n=>'1',M1_n=>ca(0),MREQ_n=>ca(1),IORQ_n=>ca(2),RD_n=>ca(3),WR_n=>ca(4),RFSH_n=>ca(5),HALT_n=>ca(6),BUSAK_n=>ca(7),A=>a,update_addr=>open,DI=>di,DO=>doa,Data_Reverse=>open);
 extended:entity work.G80A_eZ80 generic map(DATA_EXTENDED=>EXTENSIONS) port map(RESET_n=>reset_n,CLK_n=>clk,clk_enable=>ce,clk_falling=>cf,WAIT_n=>wait_n,INT_n=>'1',NMI_n=>'1',BUSRQ_n=>'1',M1_n=>cb(0),MREQ_n=>cb(1),IORQ_n=>cb(2),RD_n=>cb(3),WR_n=>cb(4),RFSH_n=>cb(5),HALT_n=>cb(6),BUSAK_n=>cb(7),A=>b,A24=>open,update_addr=>open,DI=>di,DO=>dob,Data_Reverse=>open);
 process(all) begin di<=x"00";if not is_x(a) then if ca(2)='0' and a=x"E7E7" then di<=x"E0";else di<=mem(to_integer(unsigned(a)));end if;end if;end process;
 process(clk) begin if rising_edge(clk) and reset_n='1' and ca(1)='0' and ca(4)='0' and not is_x(a) then mem(to_integer(unsigned(a)))<=doa;end if;end process;
 process(clk) begin if falling_edge(clk) and reset_n='1' then
 assert ca=cb report "compat bus control differs from original T80" severity failure;
 assert a=b report "compat address differs from original T80" severity failure;
 if ca(4)='0' then assert doa=dob report "compat write data/registers/flags differ from original T80" severity failure;end if;
 end if;end process;
 process begin if INSERT_WAIT then wait until reset_n='1';loop wait for 700 ns;wait_n<='0';wait for 350 ns;wait_n<='1';end loop;end if;wait;end process;
 process begin wait until ca(6)='0';wait for 100 ns;assert cb(6)='0' report "compat HALT" severity failure;report "PASS locked boot profile: Z80 bytes, failed keys, stack and aliases match original T80";stop;end process;
 process begin wait for 10 ms;assert false report "compat timeout" severity failure;end process;
 end;
