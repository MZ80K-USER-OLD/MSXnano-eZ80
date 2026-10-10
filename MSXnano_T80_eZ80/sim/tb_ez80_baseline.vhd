library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_ez80_baseline is
 generic (INSERT_WAIT : boolean := false);
end;
architecture test of tb_ez80_baseline is
 signal clk : std_logic := '0';
 signal reset_n : std_logic := '0';
 signal wait_n : std_logic := '1';
 signal m1,mreq,iorq,rd,wr,rfsh,halt,busak : std_logic;
 signal a : std_logic_vector(15 downto 0);
 signal di,dout : std_logic_vector(7 downto 0);
 type memory_t is array(0 to 65535) of std_logic_vector(7 downto 0);
 signal mem : memory_t := (
 0=>x"31",1=>x"00",2=>x"F0", -- LD SP,F000
 3=>x"21",4=>x"34",5=>x"12", -- LD HL,1234
 6=>x"E5",7=>x"D1", -- PUSH HL / POP DE
 8=>x"EB", -- EX DE,HL
 9=>x"22",10=>x"00",11=>x"80", -- LD (8000),HL
 12=>x"CD",13=>x"20",14=>x"00", -- CALL 0020
 15=>x"3E",16=>x"5A",17=>x"D3",18=>x"80", -- OUT (80),A
 19=>x"DB",20=>x"81",21=>x"32",22=>x"02",23=>x"80", -- IN / store
 24=>x"76", -- HALT
 32=>x"23",33=>x"22",34=>x"03",35=>x"80",36=>x"C9", -- INC HL/store/RET
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
 assert mem(16#8000#)=x"34" and mem(16#8001#)=x"12" report "PUSH/POP or LD mismatch" severity failure;
 assert mem(16#8003#)=x"35" and mem(16#8004#)=x"12" report "CALL/subroutine mismatch" severity failure;
 assert mem(16#8002#)=x"A7" and out_seen report "I/O mismatch" severity failure;
 report "PASS baseline LD/PUSH/POP/EX/CALL/RET/IN/OUT/HALT";
 stop;
 end process;
 process begin wait for 100 us; assert false report "timeout" severity failure; end process;
end;
