from pathlib import Path
import subprocess,os,json
r=Path(__file__).resolve().parents[1];w=r/'verification_tstio_decode_r25';w.mkdir(exist_ok=True)
reference=Path(os.environ['R25_BASELINE'])/'fpga/G80A_eZ80/t80_pack_ez80.vhd' if os.environ.get('R25_BASELINE') else r/'sim/reference/r24_5_tstio/t80_pack_ez80.vhd.txt'
old=reference.read_text().replace('T80_eZ80_Pack','R25_Reference_Pack')
(w/'reference_pack.vhd').write_text(old)
tb='''library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;
entity tb_tstio_decode is end;architecture test of tb_tstio_decode is begin
process variable old:std_logic_vector(52 downto 0);variable newc:std_logic_vector(53 downto 0);variable cfg:std_logic_vector(4 downto 0);variable op:std_logic_vector(7 downto 0);variable pg,xy:std_logic_vector(1 downto 0);variable n:integer:=0;
begin
for mode_id in 0 to 3 loop for c in 0 to 31 loop for p in 0 to 3 loop for x in 0 to 3 loop for o in 0 to 255 loop
 cfg:=std_logic_vector(to_unsigned(c,5));op:=std_logic_vector(to_unsigned(o,8));pg:=std_logic_vector(to_unsigned(p,2));xy:=std_logic_vector(to_unsigned(x,2));
 old:=work.R25_Reference_Pack.Decode_Execution(op,pg,xy,cfg(0),cfg(1),cfg(2),cfg(3),cfg(4),mode_id);
 newc:=work.T80_eZ80_Pack.Decode_Execution(op,pg,xy,cfg(0),cfg(1),cfg(2),cfg(3),cfg(4),mode_id);
 assert newc(52 downto 0)=old report "old execution control changed" severity failure;
 assert (newc(53)='1')=(mode_id=0 and cfg(0)='1' and p=2 and o=116) report "TSTIO qualifier mismatch" severity failure;
 n:=n+1;
end loop;end loop;end loop;end loop;end loop;
report "PASS TSTIO DECODE vectors="&integer'image(n);wait;end process;end;
'''
(w/'tb.vhd').write_text(tb);g=os.environ.get('GHDL','ghdl')
for p in [w/'reference_pack.vhd',r/'fpga/G80A_eZ80/t80_pack_ez80.vhd',w/'tb.vhd']:
 q=subprocess.run([g,'-a','--std=08','-fsynopsys',str(p)],cwd=w,capture_output=True,text=True);assert not q.returncode,q.stderr
q=subprocess.run([g,'-r','--std=08','-fsynopsys','tb_tstio_decode','--assert-level=error'],cwd=w,capture_output=True,text=True)
out=q.stdout+q.stderr;(w/'result.log').write_text(out);assert not q.returncode and 'PASS TSTIO DECODE'in out,out
print(out)
