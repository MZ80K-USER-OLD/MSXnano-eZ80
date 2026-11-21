library ieee;use ieee.std_logic_1164.all; entity sel_ref is port(IR:in std_logic_vector(7 downto 0);ISet,XY_State:in std_logic_vector(1 downto 0);Alternate:in std_logic;Q:out std_logic_vector(20 downto 0));end; architecture rtl of sel_ref is
signal Load_Upper_Index:std_logic_vector(2 downto 0);
signal Stack_Upper_Index:std_logic_vector(2 downto 0);
signal Pair_Upper_Index:std_logic_vector(2 downto 0);
signal EX_SP_Index:std_logic_vector(2 downto 0);
signal Arith_Target:std_logic_vector(2 downto 0);
signal Arith_Source:std_logic_vector(2 downto 0);
signal Mul_Target:std_logic_vector(2 downto 0);
signal Pair_Number:std_logic_vector(1 downto 0);
begin

    Load_Upper_Index<=XY_State(1) & "11" when IR(5 downto 4)="10" and XY_State/="00" else Alternate & IR(5 downto 4);
    Stack_Upper_Index<=XY_State(1) & "11" when IR(5 downto 4)="10" and XY_State/="00" else Alternate & IR(5 downto 4);
    Pair_Upper_Index<=XY_State(1) & "11" when Pair_Number="10" and XY_State/="00" else Alternate & Pair_Number;
    EX_SP_Index<=XY_State(1) & "11" when XY_State/="00" else Alternate & "10";
    Arith_Target<=XY_State(1) & "11" when ISet="00" and XY_State/="00" else Alternate & "10";
    Arith_Source<=Arith_Target when IR(5 downto 4)="10" else Alternate & IR(5 downto 4);
    Mul_Target<=Alternate & IR(5 downto 4);
    Pair_Number<="10" when ISet="00" else IR(5 downto 4);
Q<=Load_Upper_Index&Stack_Upper_Index&Pair_Upper_Index&EX_SP_Index&Arith_Target&Arith_Source&Mul_Target;end;
library ieee;use ieee.std_logic_1164.all; entity sel_dut is port(IR:in std_logic_vector(7 downto 0);ISet,XY_State:in std_logic_vector(1 downto 0);Alternate:in std_logic;Q:out std_logic_vector(20 downto 0));end; architecture rtl of sel_dut is
signal Load_Upper_Index:std_logic_vector(2 downto 0);
signal Stack_Upper_Index:std_logic_vector(2 downto 0);
signal Pair_Upper_Index:std_logic_vector(2 downto 0);
signal EX_SP_Index:std_logic_vector(2 downto 0);
signal Arith_Target:std_logic_vector(2 downto 0);
signal Arith_Source:std_logic_vector(2 downto 0);
signal Mul_Target:std_logic_vector(2 downto 0);
signal Pair_Number:std_logic_vector(1 downto 0);
signal Pair_Raw_Index:std_logic_vector(2 downto 0);
signal HL_Resolved_Index:std_logic_vector(2 downto 0);
signal XY_Register_Index:std_logic_vector(2 downto 0);
begin
    Load_Upper_Index<=HL_Resolved_Index when IR(5 downto 4)="10" else Pair_Raw_Index;
    Stack_Upper_Index<=Load_Upper_Index;
    Pair_Upper_Index<=HL_Resolved_Index when Pair_Number="10" else Alternate & Pair_Number;
    EX_SP_Index<=HL_Resolved_Index;
    Arith_Target<=HL_Resolved_Index when ISet="00" else Alternate & "10";
    Arith_Source<=Arith_Target when IR(5 downto 4)="10" else Pair_Raw_Index;
    Mul_Target<=Pair_Raw_Index;
    Pair_Number<="10" when ISet="00" else IR(5 downto 4);

    Pair_Raw_Index<=Alternate & IR(5 downto 4);
    HL_Resolved_Index<=XY_Register_Index when XY_State/="00" else Alternate & "10";
    XY_Register_Index<=XY_State(1) & "11";
Q<=Load_Upper_Index&Stack_Upper_Index&Pair_Upper_Index&EX_SP_Index&Arith_Target&Arith_Source&Mul_Target;end;
library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;
entity tb_select is end;architecture test of tb_select is
signal IR:std_logic_vector(7 downto 0);signal pg,xy:std_logic_vector(1 downto 0);signal alt:std_logic;signal qr,qd:std_logic_vector(20 downto 0);
begin
a:entity work.sel_ref port map(IR,pg,xy,alt,qr);
b:entity work.sel_dut port map(IR,pg,xy,alt,qd);
process begin
for op in 0 to 255 loop for page in 0 to 3 loop for prefix in 0 to 3 loop for bank in 0 to 1 loop
IR<=std_logic_vector(to_unsigned(op,8));pg<=std_logic_vector(to_unsigned(page,2));xy<=std_logic_vector(to_unsigned(prefix,2));
if bank=0 then alt<='0';else alt<='1';end if;
wait for 1 ns;assert qr=qd report "selection truth table mismatch" severity failure;
end loop;end loop;end loop;end loop;
report "PASS SELECT_TRUTH 8192 combinations";wait;end process;end;
