library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_pc24 is
 generic(INSERT_WAIT:boolean:=false; WIDE_FETCH:boolean:=true; BOOT_BANK:natural:=0);
end;
architecture test of tb_pc24 is
 signal clk:std_logic:='0';
 signal reset_n:std_logic:='0';
 signal wait_n:std_logic:='1';
 signal ce,cf:std_logic;
 signal phase:natural range 0 to 15:=0;
 signal a:std_logic_vector(15 downto 0);
 signal a24:std_logic_vector(23 downto 0);
 signal di,dout:std_logic_vector(7 downto 0);
 signal m1,mreq,iorq,rd,wr,rfsh,halt,busak:std_logic;
 type results_t is array(0 to 3) of std_logic_vector(7 downto 0);
 signal results:results_t:=(others=>x"A5");
 signal seen_cross:boolean:=false;
 function boot return natural is
 begin
 if WIDE_FETCH then return BOOT_BANK*65536+65532; else return 65532; end if;
 end;
 constant START_ADDR:natural:=boot;
 function next_addr(i:natural) return natural is
 begin
 if WIDE_FETCH then return (START_ADDR+i) mod 16777216;
 else return (START_ADDR+i) mod 65536; end if;
 end;
 type code_t is array(natural range <>) of std_logic_vector(7 downto 0);
 constant code:code_t:=(x"5B",x"21",x"56",x"34",x"12",x"49",x"22",x"00",x"80",x"76");
begin
 clk<=not clk after 5 ns;
 reset_n<='1' after 100 ns;
 process(clk) begin
 if rising_edge(clk) then
  if reset_n='0' then phase<=0;else phase<=(phase+1) mod 16;end if;
 end if;
 end process;
 ce<='1' when phase=0 else '0';
 cf<='1' when phase=8 else '0';
 dut:entity work.G80A_eZ80
 generic map(FETCH24=>WIDE_FETCH,RESET_PC=>std_logic_vector(to_unsigned(BOOT_BANK*65536+65532,24)))
 port map(RESET_n=>reset_n,CLK_n=>clk,clk_enable=>ce,clk_falling=>cf,WAIT_n=>wait_n,
 INT_n=>'1',NMI_n=>'1',BUSRQ_n=>'1',M1_n=>m1,MREQ_n=>mreq,IORQ_n=>iorq,
 RD_n=>rd,WR_n=>wr,RFSH_n=>rfsh,HALT_n=>halt,BUSAK_n=>busak,A=>a,A24=>a24,
 update_addr=>open,DI=>di,DO=>dout,Data_Reverse=>open);
 process(all)
 begin
 di<=x"00";
 if not is_x(a24) and mreq='0' and rd='0' then
  for i in code'range loop
   if to_integer(unsigned(a24))=next_addr(i) then di<=code(i);end if;
  end loop;
 end if;
 end process;
 process(clk)
 variable pos:natural;
 begin
 if rising_edge(clk) and reset_n='1' and not is_x(a24) then
  assert a24(15 downto 0)=a report "legacy A and A24 low mismatch" severity failure;
  if rfsh='0' then
   assert a24(23 downto 16)=x"00" report "refresh bank mismatch" severity failure;
  end if;
  if mreq='0' and rd='0' and to_integer(unsigned(a24))=next_addr(4) then seen_cross<=true;end if;
  if mreq='0' and wr='0' then
   pos:=to_integer(unsigned(a24));
   assert pos>=16#8000# and pos<=16#8002# report "data store left bank zero or overran" severity failure;
   results(pos-16#8000#)<=dout;
  end if;
 end if;
 end process;
 process begin
 if INSERT_WAIT then
 wait until reset_n='1';
 loop wait for 700 ns;wait_n<='0';wait for 350 ns;wait_n<='1';end loop;
 end if;
 wait;
 end process;
 process begin
 wait until halt='0';wait for 100 ns;
 assert seen_cross report "did not read immediate past FFFF boundary" severity failure;
 assert results(0)=x"56" and results(1)=x"34" and results(2)=x"12" and results(3)=x"A5"
 report "cross-boundary immediate or bank-zero store mismatch" severity failure;
 report "PASS PC fetch boundary, bank0 data, refresh, legacy address";
 stop;
 end process;
 process begin wait for 1 ms;assert false report "PC24 timeout" severity failure;end process;
end;
