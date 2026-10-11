library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_jump24 is
 generic(INSERT_WAIT:boolean:=false; CONDITION:natural:=0; TAKEN:boolean:=true);
end;
architecture test of tb_jump24 is
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
 signal seen_hl,seen_ix,seen_iy,seen_short:boolean:=false;
 function opcode return std_logic_vector is
 begin return std_logic_vector(to_unsigned(16#C2#+CONDITION*8,8));end;
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
 -- First absolute JP consumes its bank byte at 020000.
 constant first:code_t:=(x"5B",x"C3",x"56",x"34",x"12");
 constant conditional:code_t:=(x"3E",init_a,x"B7",carry_op,x"5B",opcode,x"00",x"00",x"23");
 constant fallback:code_t:=(x"5B",x"C3",x"00",x"00",x"23");
 constant via_hl:code_t:=(x"5B",x"21",x"78",x"56",x"34",x"5B",x"E9");
 constant via_ix:code_t:=(x"5B",x"DD",x"21",x"89",x"67",x"45",x"5B",x"DD",x"E9");
 constant via_iy:code_t:=(x"5B",x"FD",x"21",x"9A",x"78",x"56",x"5B",x"FD",x"E9");
 constant near_jump:code_t:=(x"C3",x"00",x"90");

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
 generic map(FETCH24=>true,RESET_PC=>x"01FFFC")
 port map(RESET_n=>reset_n,CLK_n=>clk,clk_enable=>ce,clk_falling=>cf,WAIT_n=>wait_n,
 INT_n=>'1',NMI_n=>'1',BUSRQ_n=>'1',M1_n=>m1,MREQ_n=>mreq,IORQ_n=>iorq,
 RD_n=>rd,WR_n=>wr,RFSH_n=>rfsh,HALT_n=>halt,BUSAK_n=>busak,A=>a,A24=>a24,
 update_addr=>open,DI=>di,DO=>dout,Data_Reverse=>open);
 process(all)
 begin
 di<=x"00";
 if not is_x(a24) and mreq='0' and rd='0' then
  for i in first'range loop
   if to_integer(unsigned(a24))=16#01FFFC#+i then di<=first(i);end if;
  end loop;
  for i in conditional'range loop
   if to_integer(unsigned(a24))=16#123456#+i then di<=conditional(i);end if;
  end loop;
  for i in fallback'range loop
   if to_integer(unsigned(a24))=16#12345F#+i then di<=fallback(i);end if;
  end loop;
  for i in via_hl'range loop
   if to_integer(unsigned(a24))=16#230000#+i then di<=via_hl(i);end if;
  end loop;
  for i in via_ix'range loop
   if to_integer(unsigned(a24))=16#345678#+i then di<=via_ix(i);end if;
  end loop;
  for i in via_iy'range loop
   if to_integer(unsigned(a24))=16#456789#+i then di<=via_iy(i);end if;
  end loop;
  for i in near_jump'range loop
   if to_integer(unsigned(a24))=16#56789A#+i then di<=near_jump(i);end if;
  end loop;
  if a24=x"569000" then di<=x"76";end if;
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
  assert wr='1' report "jump test unexpectedly wrote memory" severity failure;
  if mreq='0' and rd='0' then
   pos:=to_integer(unsigned(a24));
   if pos=16#020000# then seen_cross<=true;end if;
   if pos=16#12345F# then
    assert not TAKEN report "taken conditional JP fell through" severity failure;
    seen_short<=true;
   end if;
   if pos=16#230000# then seen_hl<=true;end if;
   if pos=16#345678# then seen_ix<=true;end if;
   if pos=16#456789# then seen_iy<=true;end if;
   assert (pos>=16#01FFFC# and pos<=16#020000#)
    or (pos>=16#123456# and pos<=16#123463#)
    or (pos>=16#230000# and pos<=16#230006#)
    or (pos>=16#345678# and pos<=16#345680#)
    or (pos>=16#456789# and pos<=16#456791#)
    or (pos>=16#56789A# and pos<=16#56789C#)
    or pos=16#569000# or pos=16#569001# report "unexpected jump fetch address " & integer'image(pos) severity failure;
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
 assert seen_hl and seen_ix and seen_iy report "missing register jump target" severity failure;
 assert (TAKEN or seen_short) report "untaken condition skipped fallthrough" severity failure;
 assert a24=x"569001" or a24=x"569000" or rfsh='0' report "wrong HALT bank" severity failure;
 report "PASS long JP, all conditional flags, HL/IX/IY JP, near bank, boundary, WAIT";
 stop;
 end process;
 process begin wait for 1 ms;assert false report "PC24 timeout" severity failure;end process;
end;
