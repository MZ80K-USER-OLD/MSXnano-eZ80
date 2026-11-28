from pathlib import Path
import os,re,subprocess,json
R=Path(__file__).resolve().parents[1];W=R/'verification_block_arithmetic_r33';W.mkdir(exist_ok=True)
s=(R/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
# Test the actual concurrent assignments, extracted from the released CPU RTL.
parts=[]
for name in ['Pair_Low_Wrap','Block_Result_Zero','Upper_Inc_Byte']:
 m=re.search(r'    '+name+r'<=.*?;',s,re.S);assert m,name
 parts.append(m[0])
v='''library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity tb_block_arithmetic_r33 is end;
architecture test of tb_block_arithmetic_r33 is
 signal Reg24A:std_logic_vector(23 downto 0):=(others=>'0');
 signal RegBusA:std_logic_vector(15 downto 0);
 signal IncDec_16:std_logic_vector(3 downto 0):=(others=>'0');
 signal Pair_Low_Wrap,Block_Result_Zero:std_logic;
 signal Upper_Inc_Byte:std_logic_vector(7 downto 0);
begin
 RegBusA<=Reg24A(15 downto 0);
'''+ '\n'.join(parts)+'''
 process
   variable tested:natural:=0;
   procedure check(v:natural;d:natural) is
     variable expected:unsigned(23 downto 0);
     variable effective_upper:std_logic_vector(7 downto 0);
   begin
     Reg24A<=std_logic_vector(to_unsigned(v,24));
     if d=1 then IncDec_16<="1000";else IncDec_16<="0000";end if;
     wait for 1 ns;
     if d=1 then expected:=to_unsigned(v,24)-1;
     else expected:=to_unsigned(v,24)+1;end if;
     -- No upper write keeps its old value; a boundary writes the shared adder.
     if Pair_Low_Wrap='1' then effective_upper:=Upper_Inc_Byte;
     else effective_upper:=Reg24A(23 downto 16);end if;
     assert effective_upper=std_logic_vector(expected(23 downto 16))
       report "upper mismatch at "&integer'image(v)&" dir "&integer'image(d) severity failure;
     assert (Block_Result_Zero='1')=(expected=0)
       report "zero mismatch at "&integer'image(v) severity failure;
     assert (Pair_Low_Wrap='1')=(expected(23 downto 16)/=unsigned(Reg24A(23 downto 16)))
       report "boundary mismatch" severity failure;
     tested:=tested+1;
   end;
   type integers is array(natural range <>)of natural;
   constant high_values:integers:=(0,1,255);
   constant low_values:integers:=(0,1,65534,65535,16#1234#);
 begin
   -- Exhaust every lower16 input; cover upper wrap/borrow and 24-bit zero.
   for d in 0 to 1 loop
     for u in high_values'range loop
       for l in 0 to 65535 loop check(high_values(u)*65536+l,d);end loop;
     end loop;
     -- Exhaust every upper input at the boundary and non-boundary classes.
     for u in 0 to 255 loop
       for l in low_values'range loop check(u*65536+low_values(l),d);end loop;
     end loop;
   end loop;
   report "PASS R33 actual RTL arithmetic cases="&integer'image(tested);
   wait;
 end process;
end;
'''
(W/'tb.vhd').write_text(v)
g=os.environ['GHDL']
for args in [['-a','--std=93','-fsynopsys','tb.vhd'],['-e','--std=93','-fsynopsys','tb_block_arithmetic_r33'],['-r','--std=93','-fsynopsys','tb_block_arithmetic_r33','--assert-level=error']]:
 p=subprocess.run([g,*args],cwd=W,capture_output=True,text=True);out=p.stdout+p.stderr
 assert p.returncode==0,out
 if args[0]=='-r':(W/'run.log').write_text(out);assert 'cases=395776'in out,out;print(out.strip(),flush=True)
(W/'result.json').write_text(json.dumps(dict(cases=395776,actual_RTL_assignments=True,upper_exhaustive_at_boundary_classes=True,lower16_exhaustive_at_upper_wrap_classes=True,hardware=False),indent=2)+'\n')
