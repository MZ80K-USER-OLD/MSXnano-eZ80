from pathlib import Path
import os,re,subprocess,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_matrix_truth_r14_1';w.mkdir(exist_ok=True)
ports="Legacy_Write : in std_logic; Write_Class : in std_logic_vector(7 downto 0); ISet : in std_logic_vector(1 downto 0); MCycle : in std_logic_vector(2 downto 0); Ext_Active,Data_Long,Stream_Long,ADL_Mode,Has_Width,IntCycle,NMICycle,Branch_Condition : in std_logic; Write : out std_logic"
for label,path in [('baseline',r/'doc/r14_decode_baseline/t80_mcode_ez80.vhd.txt'),('matrix',r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd')]:
 s=path.read_text();s=s[s.index('    process(Legacy_Write'):s.rfind('end;')]
 code="library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;entity "+label+" is generic(Mode:integer:=0);port("+ports+");end;architecture test of "+label+" is begin\n"+s+"end;\n"
 (w/(label+'.vhd')).write_text(code)
s="""library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;
entity tb_matrix_truth is generic(LEGACY_VALUE:integer:=0);end;
architecture test of tb_matrix_truth is
signal Legacy_Write : std_logic;
signal Write_Class:std_logic_vector(7 downto 0);signal ISet:std_logic_vector(1 downto 0);signal MCycle:std_logic_vector(2 downto 0);
signal Ext_Active,Data_Long,Stream_Long,ADL_Mode,Has_Width,IntCycle,NMICycle,Branch_Condition:std_logic;
signal old_w,new_w:std_logic_vector(3 downto 0);
begin
Legacy_Write<='0' when LEGACY_VALUE=0 else '1';
"""
for i in range(4):
 for label,out in [('baseline','old_w'),('matrix','new_w')]:
  names=['Legacy_Write','Write_Class','ISet','MCycle','Ext_Active','Data_Long','Stream_Long','ADL_Mode','Has_Width','IntCycle','NMICycle','Branch_Condition']
  s+=f"u_{label}_{i}:entity work.{label} generic map(Mode=>{i}) port map("+','.join(n+'=>'+n for n in names)+f",Write=>{out}({i}));\n"
s+="""process variable p:std_logic_vector(7 downto 0);variable checks:integer:=0;begin
for c in 0 to 255 loop for i in 0 to 3 loop for m in 0 to 7 loop for pr in 0 to 255 loop
Write_Class<=std_logic_vector(to_unsigned(c,8));ISet<=std_logic_vector(to_unsigned(i,2));MCycle<=std_logic_vector(to_unsigned(m,3));p:=std_logic_vector(to_unsigned(pr,8));
Ext_Active<=p(0);Data_Long<=p(1);Stream_Long<=p(2);ADL_Mode<=p(3);Has_Width<=p(4);Branch_Condition<=p(5);IntCycle<=p(6);NMICycle<=p(7);
wait for 1 ns;
assert old_w=new_w report "matrix truth mismatch class="&integer'image(c)&" ISet="&integer'image(i)&" MC="&integer'image(m)&" profile="&integer'image(pr) severity failure;
checks:=checks+4;
end loop;end loop;end loop;end loop;
report "PASS matrix truth checks="&integer'image(checks) severity note;wait;end process;end;
"""
(w/'tb.vhd').write_text(s);g=os.environ.get('GHDL','ghdl')
for n in ['baseline.vhd','matrix.vhd','tb.vhd']:
 a=subprocess.run([g,'-a','--std=08',str(w/n)],cwd=w,capture_output=True,text=True);assert a.returncode==0,a.stderr
rows=[]
for legacy in [0,1]:
 a=subprocess.run([g,'-r','--std=08','tb_matrix_truth',f'-gLEGACY_VALUE={legacy}','--assert-level=error'],cwd=w,capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;(w/f'legacy{legacy}.log').write_text(out)
 assert a.returncode==0 and 'checks=8388608' in out,out
 rows.append(dict(Legacy_Write=legacy,checks=8388608));print('PASS matrix all class/phase/mode/width/IRQ profiles; Legacy_Write=',legacy,flush=True)
(r/'verification_matrix_truth_r14_1_result.json').write_text(json.dumps(dict(fresh_runs=2,expected_failure_runs=0,total_boolean_comparisons=16777216,all_256_Write_Class_values=True,Mode_values=[0,1,2,3],rows=rows,extracted_actual_baseline_and_candidate_processes=True,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
