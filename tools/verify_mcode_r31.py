from pathlib import Path
import re,os,subprocess,json
R=Path(__file__).resolve().parents[1];W=R/'verification_mcode_r31';W.mkdir(exist_ok=True)
pkg=(R/'sim/reference_r30/t80_pack_ez80.vhd').read_text().replace('T80_eZ80_Pack','Ref_Pack')
ref=(R/'sim/reference_r30/t80_mcode_ez80.vhd').read_text().replace('T80_eZ80_Pack','Ref_Pack').replace('T80_MCode_eZ80','Ref_Mcode')
(W/'ref_pack.vhd').write_text(pkg);(W/'ref_mcode.vhd').write_text(ref)
s=(R/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text();ports=s.split('        port(',1)[1].split('        );',1)[0];ports=re.sub(r'--[^\n]*','',ports)
ins=[];outs=[]
for line in ports.split(';'):
 m=re.fullmatch(r'\s*([\w, ]+)\s*:\s*(in|out)\s+(.*?)\s*',line,re.S)
 if m:
  for name in m[1].replace(' ','').split(','):(ins if m[2]=='in'else outs).append((name,m[3]))
assert len(outs)>40 and any(n=='Exec_Control'for n,t in ins)
sigs=[]
for n,t in ins:
 if n=='Exec_Control':sigs+=['signal ec_new:work.T80_eZ80_Pack.exec_control_t;signal ec_old:work.Ref_Pack.exec_control_t;']
 else:sigs.append('signal '+n+':'+t+(' := (others=>\'0\');'if'vector'in t else" := '0';"))
for n,t in outs:sigs.append(f'signal new_{n},old_{n}:{t};')
instances=[]
for label,entity in [('new','T80_MCode_eZ80'),('old','Ref_Mcode')]:
 bindings=[n+'=>'+('ec_new'if label=='new'else'ec_old')if n=='Exec_Control'else n+'=>'+n for n,t in ins]
 bindings +=[n+'=>'+label+'_'+n for n,t in outs]
 instances.append(label+'_dut:entity work.'+entity+' generic map(Mode=>0)port map('+','.join(bindings)+');')
checks='\n'.join(f'assert new_{n}=old_{n} report "mcode mismatch {n} op="&integer\'image(op)&" pg="&integer\'image(pg)&" ctx="&integer\'image(ctx)&" cycle="&integer\'image(cy) severity failure;'for n,t in outs)
tb='''library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;
entity tb_mcode_r31 is end;architecture sim of tb_mcode_r31 is
'''+ '\n'.join(sigs)+ '\nbegin\n'+'\n'.join(instances)+'''
process variable o:std_logic_vector(7 downto 0);variable p,x:std_logic_vector(1 downto 0);variable c:std_logic_vector(4 downto 0);variable count:natural:=0;begin
for op in 0 to 255 loop for pg in 0 to 3 loop for xy in 0 to 3 loop for ctx in 0 to 31 loop
 o:=std_logic_vector(to_unsigned(op,8));p:=std_logic_vector(to_unsigned(pg,2));x:=std_logic_vector(to_unsigned(xy,2));c:=std_logic_vector(to_unsigned(ctx,5));
 IR<=o;ISet<=p;XY_State<=x;Write_Class<=work.T80_eZ80_Pack.Classify_Write(o);
 ec_new<=work.T80_eZ80_Pack.Decode_Execution(o,p,x,c(0),c(1),c(2),c(3),c(4),0);
 ec_old<=work.Ref_Pack.Decode_Execution(o,p,x,c(0),c(1),c(2),c(3),c(4),0);
 Ext_Active<=c(0);ADL_Mode<=c(1);Data_Long<=c(2);Stream_Long<=c(3);Has_Width<=c(4);
 for cy in 1 to 7 loop for irq in 0 to 2 loop for branch in 0 to 1 loop
 MCycle<=std_logic_vector(to_unsigned(cy,3));IntCycle<='0';NMICycle<='0';Interrupt_Long<='0';
 if irq=1 then IntCycle<='1';Interrupt_Long<=c(0)and c(1);elsif irq=2 then NMICycle<='1';Interrupt_Long<=c(0)and c(1);end if;
 if branch=0 then Branch_Condition<='0';F<=x"A5";else Branch_Condition<='1';F<=x"5A";end if;
 Interrupt_Mode<=std_logic_vector(to_unsigned(ctx mod 3,2));wait for 1 ns;
'''+checks+'''
 count:=count+1;
 end loop;end loop;end loop;end loop;end loop;end loop;end loop;
 report "PASS mcode_r31 cases="&integer'image(count);wait;end process;end;
'''
(W/'tb.vhd').write_text(tb)
g=os.environ['GHDL']
for p in [W/'ref_pack.vhd',W/'ref_mcode.vhd',R/'fpga/G80A_eZ80/t80_pack_ez80.vhd',R/'fpga/G80A_eZ80/t80_mcode_ez80.vhd',W/'tb.vhd']:
 a=subprocess.run([g,'-a','--std=08','-fsynopsys',str(p)],cwd=W,capture_output=True,text=True);assert not a.returncode,a.stderr
a=subprocess.run([g,'-r','--std=08','-fsynopsys','tb_mcode_r31','--assert-level=error'],cwd=W,capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;(W/'run.log').write_text(out)
assert not a.returncode and 'PASS mcode_r31'in out,out[-1500:]
(W/'result.json').write_text(json.dumps(dict(cases=256*4*4*32*7*3*2,output_ports=len(outs),mode=0,baseline='R30',passed=True,terminal_descriptor_consistent=True,all_flags_exhaustive=False),indent=2)+'\n')
print(out.strip())
