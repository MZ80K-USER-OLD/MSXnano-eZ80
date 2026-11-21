from pathlib import Path
import os,subprocess,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_load_decode_r24_2';w.mkdir(exist_ok=True)
s='''library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;use work.T80_eZ80_Pack.all;
entity tb_load_decode is end;architecture sim of tb_load_decode is begin
process variable c:exec_control_t;variable v:std_logic_vector(4 downto 0);variable op:std_logic_vector(7 downto 0);variable xy:std_logic_vector(1 downto 0);variable imm,ab,ind:boolean;variable n:integer:=0;
begin
for mode_id in 0 to 3 loop for cfg in 0 to 31 loop for pg in 0 to 3 loop for x in 0 to 3 loop for o in 0 to 255 loop
v:=std_logic_vector(to_unsigned(cfg,5));op:=std_logic_vector(to_unsigned(o,8));xy:=std_logic_vector(to_unsigned(x,2));
c:=Decode_Execution(op,std_logic_vector(to_unsigned(pg,2)),xy,v(0),v(1),v(2),v(3),v(4),mode_id);
imm:=mode_id=0 and v(0)='1' and pg=0 and (o=1 or o=17 or o=33 or o=49) and not(x/=0 and o=49);
ab:=mode_id=0 and v(0)='1' and ((pg=0 and o=42) or(pg=2 and(o=75 or o=91 or o=107 or o=123)));
ind:=mode_id=0 and v(0)='1' and (pg=2 or(pg=0 and x/=0)) and(o=7 or o=23 or o=39 or o=55 or o=49);
assert (c(EC_LOAD_IMM)='1')=imm and (c(EC_LOAD_ABS)='1')=ab and (c(EC_LOAD_IND)='1')=ind report "load family decode mismatch" severity failure;
assert not((imm and ab)or(imm and ind)or(ab and ind)) report "load families overlap" severity failure;
if imm or ab or ind then assert c(EC_EX_SP)='0' report "load collector overlaps EX(SP) work ownership" severity failure;end if;
n:=n+1;
end loop;end loop;end loop;end loop;end loop;
report "PASS load decode vectors="&integer'image(n);wait;end process;end;
'''
(w/'tb.vhd').write_text(s);g=os.environ.get('GHDL','ghdl');log=''
for p in [r/'fpga/G80A_eZ80/t80_pack_ez80.vhd',w/'tb.vhd']:
 a=subprocess.run([g,'-a','--std=08','-fsynopsys',str(p)],cwd=w,capture_output=True,text=True);assert not a.returncode,a.stderr
out=subprocess.run([g,'-r','--std=08','-fsynopsys','tb_load_decode','--assert-level=error'],cwd=w,capture_output=True,text=True);log=out.stdout+out.stderr;(w/'result.log').write_text(log);assert not out.returncode and 'PASS load decode vectors=524288'in log,log
(w/'result.json').write_text(json.dumps(dict(vectors=524288,load_family_exclusivity=True,EX_SP_work_exclusivity=True,all_modes=True,package_sha256=hashlib.sha256((r/'fpga/G80A_eZ80/t80_pack_ez80.vhd').read_bytes()).hexdigest(),GOWIN=False),indent=2)+'\n');print(log.strip())
