from pathlib import Path
import re,subprocess,os
r=Path(__file__).resolve().parent.parent;w=r/'verification_mcode_r21_1';w.mkdir(exist_ok=True)
old=(r/'sim/reference/t80_mcode_r21.vhd').read_text();(w/'old.vhd').write_text(old.replace('T80_MCode_eZ80','T80_MCode_old'))
s=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text();ports=s[s.index('        port('):s.index('end T80_MCode_eZ80')];ports=re.sub(r'--[^\n]*','',ports);ports=ports[ports.index('(')+1:ports.rindex(')')]
rows=[]
for row in ports.split(';'):
 m=re.fullmatch(r'\s*([\w, ]+)\s*:\s*(in|out)\s+(.+?)\s*',row,re.S);assert m,row
 for n in m[1].split(','):rows.append((n.strip(),m[2],m[3].strip()))
inp=[q for q in rows if q[1]=='in'];out=[q for q in rows if q[1]=='out']
t='library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;use work.T80_eZ80_Pack.all;\nentity tb_mceq is generic(M:integer:=0);end;architecture sim of tb_mceq is\n'
for n,d,typ in inp:t+=f'signal {n}:{typ};\n'
for n,d,typ in out:t+=f'signal old_{n},new_{n}:{typ};\n'
t+='begin\n'
for tag,entity in [('old','T80_MCode_old'),('new','T80_MCode_eZ80')]:t+=f'{tag}dut:entity work.{entity} generic map(Mode=>M)port map('+','.join(n+'=>'+(n if d=='in'else tag+'_'+n)for n,d,typ in rows)+');\n'
t+='''process
variable v:std_logic_vector(5 downto 0);
variable op:std_logic_vector(7 downto 0);
variable count:integer:=0;
begin
for o in 0 to 255 loop
 op:=std_logic_vector(to_unsigned(o,8));IR<=op;Write_Class<=Classify_Write(op);
 for p in 0 to 3 loop
 ISet<=std_logic_vector(to_unsigned(p,2));
 for c in 1 to 7 loop
 MCycle<=std_logic_vector(to_unsigned(c,3));
 for cfg in 0 to 63 loop
 v:=std_logic_vector(to_unsigned(cfg,6));
 Ext_Active<=v(0);Data_Long<=v(1);Stream_Long<=v(2);ADL_Mode<=v(3);Has_Width<=v(1) xor v(2);
 IntCycle<=v(4);NMICycle<=v(5);XY_State<=v(3 downto 2);Interrupt_Mode<=v(1 downto 0);Branch_Condition<=v(5) xor v(0);
 F<=std_logic_vector(to_unsigned((cfg*73+o*19+c*11+p*61) mod 256,8));
 wait for 1 ns;
'''
for n,d,typ in out:t+=f'assert old_{n}=new_{n} report "mcode mismatch {n} op="&integer\'image(o)&" page="&integer\'image(p)&" cycle="&integer\'image(c)&" cfg="&integer\'image(cfg) severity failure;\n'
t+='''count:=count+1;end loop;end loop;end loop;end loop;
report "PASS mcode equivalence Mode="&integer'image(M)&" vectors="&integer'image(count);wait;end process;end;
'''
(w/'tb.vhd').write_text(t)
g=os.environ.get('GHDL','ghdl')
for f in [r/'fpga/G80A_eZ80/t80_pack_ez80.vhd',w/'old.vhd',r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd',w/'tb.vhd']:
 subprocess.run([str(g),'-a','--std=08','-fsynopsys',str(f)],cwd=w,check=True)
for m in range(4):
 a=subprocess.run([str(g),'-r','--std=08','-fsynopsys','tb_mceq',f'-gM={m}','--assert-level=error'],cwd=w,capture_output=True,text=True);(w/f'mode{m}.log').write_text(a.stdout+a.stderr);assert a.returncode==0,a.stdout+a.stderr;print(a.stdout.strip(),flush=True)
