library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_hardware_com is
 generic (INSERT_WAIT : boolean := false);
end;
architecture test of tb_hardware_com is
 signal clk : std_logic := '0';
 signal reset_n : std_logic := '0';
 signal wait_n : std_logic := '1';
 signal m1,mreq,iorq,rd,wr,rfsh,halt,busak : std_logic;
 signal a : std_logic_vector(15 downto 0);
 signal di,dout : std_logic_vector(7 downto 0);
 type memory_t is array(0 to 65535) of std_logic_vector(7 downto 0);
 signal mem : memory_t := (
 0=>x"C3",1=>x"00",2=>x"01",
 5=>x"D3",6=>x"80",7=>x"76",
 256=>x"5B",
 257=>x"21",
 258=>x"56",
 259=>x"34",
 260=>x"12",
 261=>x"49",
 262=>x"22",
 263=>x"58",
 264=>x"01",
 265=>x"5B",
 266=>x"DD",
 267=>x"21",
 268=>x"88",
 269=>x"77",
 270=>x"66",
 271=>x"49",
 272=>x"DD",
 273=>x"22",
 274=>x"5B",
 275=>x"01",
 276=>x"5B",
 277=>x"FD",
 278=>x"21",
 279=>x"BB",
 280=>x"AA",
 281=>x"99",
 282=>x"49",
 283=>x"FD",
 284=>x"22",
 285=>x"5E",
 286=>x"01",
 287=>x"5B",
 288=>x"21",
 289=>x"56",
 290=>x"34",
 291=>x"12",
 292=>x"E5",
 293=>x"D1",
 294=>x"ED",
 295=>x"53",
 296=>x"61",
 297=>x"01",
 298=>x"21",
 299=>x"CD",
 300=>x"AB",
 301=>x"22",
 302=>x"63",
 303=>x"01",
 304=>x"21",
 305=>x"58",
 306=>x"01",
 307=>x"11",
 308=>x"66",
 309=>x"01",
 310=>x"06",
 311=>x"0E",
 312=>x"1A",
 313=>x"BE",
 314=>x"C2",
 315=>x"4D",
 316=>x"01",
 317=>x"23",
 318=>x"13",
 319=>x"C3",
 320=>x"42",
 321=>x"01",
 322=>x"05",
 323=>x"C2",
 324=>x"38",
 325=>x"01",
 326=>x"11",
 327=>x"74",
 328=>x"01",
 329=>x"AF",
 330=>x"C3",
 331=>x"52",
 332=>x"01",
 333=>x"11",
 334=>x"84",
 335=>x"01",
 336=>x"3E",
 337=>x"01",
 338=>x"0E",
 339=>x"09",
 340=>x"CD",
 341=>x"05",
 342=>x"00",
 343=>x"C9",
 344=>x"00",
 345=>x"00",
 346=>x"00",
 347=>x"00",
 348=>x"00",
 349=>x"00",
 350=>x"00",
 351=>x"00",
 352=>x"00",
 353=>x"00",
 354=>x"00",
 355=>x"00",
 356=>x"00",
 357=>x"00",
 358=>x"56",
 359=>x"34",
 360=>x"12",
 361=>x"88",
 362=>x"77",
 363=>x"66",
 364=>x"BB",
 365=>x"AA",
 366=>x"99",
 367=>x"56",
 368=>x"34",
 369=>x"CD",
 370=>x"AB",
 371=>x"00",
 372=>x"45",
 373=>x"5A",
 374=>x"38",
 375=>x"30",
 376=>x"20",
 377=>x"76",
 378=>x"34",
 379=>x"3A",
 380=>x"20",
 381=>x"50",
 382=>x"41",
 383=>x"53",
 384=>x"53",
 385=>x"0D",
 386=>x"0A",
 387=>x"24",
 388=>x"45",
 389=>x"5A",
 390=>x"38",
 391=>x"30",
 392=>x"20",
 393=>x"76",
 394=>x"34",
 395=>x"3A",
 396=>x"20",
 397=>x"46",
 398=>x"41",
 399=>x"49",
 400=>x"4C",
 401=>x"0D",
 402=>x"0A",
 403=>x"24",
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
   assert a(7 downto 0)=x"80" and dout=x"00" report "OUT mismatch" severity failure;
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
 assert out_seen report "COM failed or did not report" severity failure;
 report "PASS supplied MSX-DOS COM comparison path";
 stop;
 end process;
 process begin wait for 100 us; assert false report "timeout" severity failure; end process;
end;
