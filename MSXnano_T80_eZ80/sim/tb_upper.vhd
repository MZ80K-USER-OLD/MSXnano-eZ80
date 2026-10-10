library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity tb_upper is end;
architecture test of tb_upper is
 signal clk : std_logic := '0';
 signal rst,cen,weu,weh,wel : std_logic := '0';
 signal aa,ab,ac : std_logic_vector(2 downto 0) := "000";
 signal diu,dih,dil,au,bu,cu,ah,al,bh,bl,ch,cl : std_logic_vector(7 downto 0) := x"00";
begin
 clk <= not clk after 5 ns;
 dut: entity work.T80_eZ80_Reg port map(
 Clk=>clk,CEN=>cen,RESET_U_n=>rst,WEU=>weu,DIU=>diu,DOAU=>au,DOBU=>bu,DOCU=>cu,
 WEH=>weh,WEL=>wel,AddrA=>aa,AddrB=>ab,AddrC=>ac,DIH=>dih,DIL=>dil,
 DOAH=>ah,DOAL=>al,DOBH=>bh,DOBL=>bl,DOCH=>ch,DOCL=>cl);
 process
 begin
 wait for 2 ns;
 for i in 0 to 7 loop
  aa<=std_logic_vector(to_unsigned(i,3)); wait for 1 ns;
  assert au=x"00" report "upper reset failed" severity failure;
 end loop;
 wait until falling_edge(clk);rst<='1';cen<='1';weu<='1';weh<='1';wel<='1';
 for i in 0 to 7 loop
  aa<=std_logic_vector(to_unsigned(i,3));
  diu<=std_logic_vector(to_unsigned(16#80#+i,8));dih<=x"12";dil<=x"34";
  wait until rising_edge(clk); wait until falling_edge(clk);
 end loop;
 weu<='0';weh<='0';wel<='0';
 for i in 0 to 7 loop
  aa<=std_logic_vector(to_unsigned(i,3));ab<=std_logic_vector(to_unsigned((i+1) mod 8,3));ac<=std_logic_vector(to_unsigned((i+2) mod 8,3));
  wait for 1 ns;
  assert au=std_logic_vector(to_unsigned(16#80#+i,8)) and bu=std_logic_vector(to_unsigned(16#80#+((i+1) mod 8),8)) and cu=std_logic_vector(to_unsigned(16#80#+((i+2) mod 8),8)) report "upper read ports failed" severity failure;
  assert ah=x"12" and al=x"34" report "lower storage failed" severity failure;
 end loop;
 wait until falling_edge(clk);aa<="000";weu<='1';diu<=x"FF";cen<='0';
 wait until rising_edge(clk);wait for 1 ns;
 assert au=x"80" report "CEN hold failed" severity failure;
 wait until falling_edge(clk);cen<='1';weu<='0';wel<='1';dil<=x"AB";
 wait until rising_edge(clk);wait for 1 ns;
 assert au=x"80" and ah=x"12" and al=x"AB" report "short write corrupted upper" severity failure;
 wait until falling_edge(clk);wel<='0';weu<='1';diu<=x"CD";
 wait until rising_edge(clk);wait for 1 ns;
 assert au=x"CD" and ah=x"12" and al=x"AB" report "upper write corrupted lower" severity failure;
 rst<='0';wait for 1 ns;
 assert au=x"00" and ah=x"12" and al=x"AB" report "reset isolation failed" severity failure;
 report "PASS upper storage: 8 slots, 3 read ports, CEN, byte write isolation, reset";
 stop;
 end process;
 process begin wait for 10 us;assert false report "timeout" severity failure;end process;
end;
