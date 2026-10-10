library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_long_store is
 generic (INSERT_WAIT : boolean := false);
end;
architecture test of tb_long_store is
 signal clk : std_logic := '0';
 signal reset_n : std_logic := '0';
 signal wait_n : std_logic := '1';
 signal m1,mreq,iorq,rd,wr,rfsh,halt,busak : std_logic;
 signal a : std_logic_vector(15 downto 0);
 signal di,dout : std_logic_vector(7 downto 0);
 type memory_t is array(0 to 65535) of std_logic_vector(7 downto 0);
 signal mem : memory_t := (
 0=>x"5B",
 1=>x"21",
 2=>x"56",
 3=>x"34",
 4=>x"12",
 5=>x"49",
 6=>x"22",
 7=>x"00",
 8=>x"80",
 9=>x"5B",
 10=>x"DD",
 11=>x"21",
 12=>x"88",
 13=>x"77",
 14=>x"66",
 15=>x"49",
 16=>x"DD",
 17=>x"22",
 18=>x"03",
 19=>x"80",
 20=>x"5B",
 21=>x"FD",
 22=>x"21",
 23=>x"BB",
 24=>x"AA",
 25=>x"99",
 26=>x"49",
 27=>x"FD",
 28=>x"22",
 29=>x"06",
 30=>x"80",
 31=>x"21",
 32=>x"CD",
 33=>x"AB",
 34=>x"22",
 35=>x"09",
 36=>x"80",
 37=>x"76",
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
 assert mem(16#8000#)=x"56" report "store byte 0 mismatch" severity failure;
 assert mem(16#8001#)=x"34" report "store byte 1 mismatch" severity failure;
 assert mem(16#8002#)=x"12" report "store byte 2 mismatch" severity failure;
 assert mem(16#8003#)=x"88" report "store byte 3 mismatch" severity failure;
 assert mem(16#8004#)=x"77" report "store byte 4 mismatch" severity failure;
 assert mem(16#8005#)=x"66" report "store byte 5 mismatch" severity failure;
 assert mem(16#8006#)=x"BB" report "store byte 6 mismatch" severity failure;
 assert mem(16#8007#)=x"AA" report "store byte 7 mismatch" severity failure;
 assert mem(16#8008#)=x"99" report "store byte 8 mismatch" severity failure;
 assert mem(16#8009#)=x"CD" report "store byte 9 mismatch" severity failure;
 assert mem(16#800A#)=x"AB" report "store byte 10 mismatch" severity failure;
 assert mem(16#800B#)=x"00" report "store byte 11 mismatch" severity failure;
 report "PASS 24bit HL/IX/IY stores and short restoration";
 stop;
 end process;
 process begin wait for 100 us; assert false report "timeout" severity failure; end process;
end;
