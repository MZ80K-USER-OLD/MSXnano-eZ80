library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_mixed24 is
 generic(INSERT_WAIT:boolean:=false; CONDITION:natural:=0; TAKEN:boolean:=true; STACK_TOP:natural:=196609);
end;
architecture test of tb_mixed24 is
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
 type ram_t is array(0 to 15) of std_logic_vector(7 downto 0);
 signal ram:ram_t:=(others=>x"A5");
 signal prev_wr:std_logic:='1';
 signal writes:natural:=0;
 signal seen_callee,seen_short_ret,seen_cond_fall:boolean:=false;
 function stack_address(pos:natural) return boolean is
 begin
 for k in 1 to 7 loop
  if pos=(STACK_TOP+16777216-k) mod 16777216 then return true;end if;
 end loop;
 return false;
 end;
 function opcode return std_logic_vector is
 begin return std_logic_vector(to_unsigned(16#C4#+CONDITION*8,8));end;
 function init_a return std_logic_vector is
 begin
 case CONDITION is
 when 0 => if TAKEN then return x"01";else return x"00";end if;
 when 1 => if TAKEN then return x"00";else return x"01";end if;
 when 4 => if TAKEN then return x"01";else return x"00";end if;
 when 5 => if TAKEN then return x"00";else return x"01";end if;
 when 6 => if TAKEN then return x"01";else return x"80";end if;
 when 7 => if TAKEN then return x"80";else return x"01";end if;
 when others => return x"00";
 end case;
 end;
 function carry_op return std_logic_vector is
 begin
 if (CONDITION=2 and not TAKEN) or (CONDITION=3 and TAKEN) then return x"37";
 else return x"00";end if;
 end;
 type code_t is array(natural range <>) of std_logic_vector(7 downto 0);
 constant first:code_t:=(x"31",x"00",x"90",x"5B",x"31",x"01",x"00",std_logic_vector(to_unsigned(STACK_TOP/65536,8)),
  x"00",x"00",x"00",x"00",x"00",x"52",x"CD",x"56",x"34",x"12",x"52",x"CD",x"56",x"34",x"12",x"76");
 constant conditional:code_t:=(x"3E",init_a,x"B7",carry_op,x"5B",opcode,x"00",x"00",x"23");
 constant fallback:code_t:=(x"5B",x"CD",x"00",x"00",x"23",x"5B",x"C9");
 constant callee:code_t:=(x"CD",x"10",x"00",x"5B",std_logic_vector(to_unsigned(16#C0#+CONDITION*8,8)),x"5B",x"C9");

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
 generic map(FETCH24=>true,RESET_PC=>x"000100",ENABLE_MIXED=>true)
 port map(RESET_n=>reset_n,CLK_n=>clk,clk_enable=>ce,clk_falling=>cf,WAIT_n=>wait_n,
 INT_n=>'1',NMI_n=>'1',BUSRQ_n=>'1',M1_n=>m1,MREQ_n=>mreq,IORQ_n=>iorq,
 RD_n=>rd,WR_n=>wr,RFSH_n=>rfsh,HALT_n=>halt,BUSAK_n=>busak,A=>a,A24=>a24,
 update_addr=>open,DI=>di,DO=>dout,Data_Reverse=>open);
 process(all)
 begin
 di<=x"00";
 if not is_x(a24) and mreq='0' and rd='0' then
  di<=ram(to_integer(unsigned(a24(3 downto 0))));
  if a24=x"008FFE" then di<=ram(4);elsif a24=x"008FFF" then di<=ram(5);end if;
  for i in first'range loop
   if to_integer(unsigned(a24))=16#000100#+i then di<=first(i);end if;
  end loop;
  for i in conditional'range loop
   if to_integer(unsigned(a24))=16#123456#+i then di<=conditional(i);end if;
  end loop;
  for i in fallback'range loop
   if to_integer(unsigned(a24))=16#12345F#+i and not TAKEN then di<=fallback(i);end if;
  end loop;
  if TAKEN and a24=x"12345F" then di<=x"5B";end if;
  if TAKEN and a24=x"123460" then di<=x"C9";end if;
  for i in callee'range loop
   if to_integer(unsigned(a24))=16#230000#+i then di<=callee(i);end if;
  end loop;
  if a24=x"230010" then di<=x"C9";end if;
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
  prev_wr<=wr;
  if wr='0' and prev_wr='1' then writes<=writes+1;end if;
  if mreq='0' and wr='0' then
   pos:=to_integer(unsigned(a24));
   assert stack_address(pos) or pos=16#8FFE# or pos=16#8FFF#
    report "wrong stack write address " & integer'image(pos) severity failure;
   if pos=16#8FFE# then ram(4)<=dout;elsif pos=16#8FFF# then ram(5)<=dout;else ram(pos mod 16)<=dout;end if;
  end if;
  if mreq='0' and rd='0' then
   pos:=to_integer(unsigned(a24));
   if pos=16#000112# then seen_cross<=true;end if;
   if pos=16#230000# then seen_callee<=true;end if;
   if pos=16#230010# then seen_short_ret<=true;end if;
   if pos=16#230005# then
    assert not TAKEN report "taken conditional RET fell through" severity failure;
    seen_cond_fall<=true;
   end if;
   if pos=16#123461# then assert not TAKEN report "taken conditional CALL fell through" severity failure;end if;
   assert (pos>=16#000100# and pos<=16#000118#)
    or (pos>=16#123456# and pos<=16#123465#)
    or (pos>=16#230000# and pos<=16#230007#)
    or pos=16#230010# or pos=16#230011#
    or stack_address(pos) or pos=16#8FFE# or pos=16#8FFF#
    report "wrong CALL/RET address " & integer'image(pos) severity failure;
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
 assert ram(14)=x"02" and ram(10)=x"03" report "mixed mode markers mismatch" severity failure;
 assert writes=18 report "wrong mixed stack write count" severity failure;
 assert seen_callee and seen_short_ret report "missing mixed nested call" severity failure;
 assert TAKEN or seen_cond_fall report "untaken RET skipped fallthrough" severity failure;
 assert ram(15)=x"17" and ram(0)=x"01" report "short return address mismatch" severity failure;
 assert ram(11)=x"5F" or ram(11)=x"64" report "long inner return low mismatch" severity failure;
 assert ram(12)=x"34" and ram(13)=x"12" report "long inner return bank mismatch" severity failure;
 assert ram(4)=x"03" and ram(5)=x"00" report "mixed call changed SPS" severity failure;
 assert ram(9)=x"A5" and ram(1)=x"A5" report "mixed stack guards overwritten" severity failure;
 report "PASS short-to-long CALL, 02/03 RET, repeated mode switch, conditional, WAIT";
 stop;
 end process;
 process begin wait for 1 ms;assert false report "PC24 timeout" severity failure;end process;
end;
