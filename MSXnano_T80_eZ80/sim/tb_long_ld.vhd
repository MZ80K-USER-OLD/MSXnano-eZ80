library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_long_ld is
 generic (INSERT_WAIT : boolean := false);
end;
architecture test of tb_long_ld is
 signal clk : std_logic := '0';
 signal reset_n : std_logic := '0';
 signal wait_n : std_logic := '1';
 signal m1,mreq,iorq,rd,wr,rfsh,halt,busak : std_logic;
 signal a : std_logic_vector(15 downto 0);
 signal di,dout : std_logic_vector(7 downto 0);
 type memory_t is array(0 to 65535) of std_logic_vector(7 downto 0);
 signal mem : memory_t := (
 0=>x"5B",
 1=>x"01",
 2=>x"34",
 3=>x"12",
 4=>x"56",
 5=>x"ED",
 6=>x"43",
 7=>x"00",
 8=>x"80",
 9=>x"5B",
 10=>x"11",
 11=>x"78",
 12=>x"56",
 13=>x"9A",
 14=>x"ED",
 15=>x"53",
 16=>x"02",
 17=>x"80",
 18=>x"5B",
 19=>x"21",
 20=>x"BC",
 21=>x"9A",
 22=>x"BC",
 23=>x"22",
 24=>x"04",
 25=>x"80",
 26=>x"5B",
 27=>x"DD",
 28=>x"21",
 29=>x"F0",
 30=>x"DE",
 31=>x"DE",
 32=>x"DD",
 33=>x"22",
 34=>x"06",
 35=>x"80",
 36=>x"5B",
 37=>x"FD",
 38=>x"21",
 39=>x"24",
 40=>x"13",
 41=>x"F0",
 42=>x"FD",
 43=>x"22",
 44=>x"08",
 45=>x"80",
 46=>x"21",
 47=>x"AA",
 48=>x"55",
 49=>x"22",
 50=>x"0A",
 51=>x"80",
 52=>x"76",
 others=>x"00");
 signal out_seen : boolean := false;
begin
 clk <= not clk after 5 ns;
 reset_n <= '1' after 100 ns;
 dut: entity work.G80A_eZ80 port map(
 RESET_n=>reset_n,CLK_n=>clk,clk_enable=>'1',clk_falling=>'1',WAIT_n=>wait_n,
 INT_n=>'1',NMI_n=>'1',BUSRQ_n=>'1',M1_n=>m1,MREQ_n=>mreq,IORQ_n=>iorq,
 RD_n=>rd,WR_n=>wr,RFSH_n=>rfsh,HALT_n=>halt,BUSAK_n=>busak,A=>a,
 update_addr=>open,DI=>di,DO=>dout,Data_Reverse=>open);
 process(all)
 begin
 di <= x"FF";
 if not is_x(a) then
  if mreq='0' and rd='0' then di<=mem(to_integer(unsigned(a)));
  elsif iorq='0' and rd='0' then di<=x"A7"; end if;
 end if;
 end process;
 process(clk)
 begin
 if rising_edge(clk) and reset_n='1' then
  if mreq='0' and wr='0' then mem(to_integer(unsigned(a)))<=dout; end if;
  if iorq='0' and wr='0' then
   assert a(7 downto 0)=x"80" and dout=x"5A" report "OUT mismatch" severity failure;
   out_seen<=true;
  end if;
 end if;
 end process;
 process
 begin
 if INSERT_WAIT then
  wait until reset_n='1';
  loop
   wait for 70 ns; wait_n<='0'; wait for 30 ns; wait_n<='1';
  end loop;
 end if;
 wait;
 end process;
 process
 begin
 wait until halt='0'; wait for 20 ns;
 assert mem(16#8000#)=x"34" and mem(16#8001#)=x"12" report "BC low mismatch" severity failure;
 assert mem(16#8002#)=x"78" and mem(16#8003#)=x"56" report "DE low mismatch" severity failure;
 assert mem(16#8004#)=x"BC" and mem(16#8005#)=x"9A" report "HL low mismatch" severity failure;
 assert mem(16#8006#)=x"F0" and mem(16#8007#)=x"DE" report "IX low mismatch" severity failure;
 assert mem(16#8008#)=x"24" and mem(16#8009#)=x"13" report "IY low mismatch" severity failure;
 assert mem(16#800A#)=x"AA" and mem(16#800B#)=x"55" report "suffix not cleared" severity failure;
 report "PASS long immediate instruction stream and short-width restoration";
 stop;
 end process;
 process begin wait for 100 us; assert false report "timeout" severity failure; end process;
end;
