from pathlib import Path
import re,subprocess,os,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_write_r14';w.mkdir(exist_ok=True)
b=(r/'doc/r13_1_mixed_baseline/t80_mcode_ez80.vhd.txt').read_text()
(w/'reference.vhd').write_text(b.replace('T80_MCode_eZ80','T80_MCode_Reference'))
port=b[b.index('        port(')+13:b.index('end T80_MCode_eZ80;')];port=port[:port.rfind(');')]
ports=[]
for line in port.splitlines():
 line=line.split('--')[0];m=re.search(r'^\s*([\w, ]+)\s*:\s*(in|out)\s+(std_logic(?:_vector\(\d+ downto \d+\))?)',line)
 if m:
  for n in m[1].split(','):
   if n.strip()!='Write_Class':ports.append((n.strip(),m[2],m[3]))
assert len(ports)>60,len(ports)
inputs=[x for x in ports if x[1]=='in'];outputs=[x for x in ports if x[1]=='out']
s='''library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.T80_eZ80_Pack.all;
entity tb_write_r14 is generic(PROFILE_MODE:integer:=0;FAULT:boolean:=false);end;
architecture test of tb_write_r14 is
'''
for n,_,t in inputs:s+=f"signal {n} : {t} := "+("'0'" if t=='std_logic' else "(others=>'0')")+";\n"
for n,_,t in outputs:s+=f'signal old_{n}, new_{n} : {t};\n'
s+='signal wc : std_logic_vector(7 downto 0);\nbegin\n'
s+='wc<=x"00" when FAULT and IR=x"32" else Classify_Write(IR);\n'
for label,entity,prefix in [('ref','T80_MCode_Reference','old_'),('dut','T80_MCode_eZ80','new_')]:
 args=[f'{n}=>{n if dr=="in" else prefix+n}' for n,dr,t in ports]
 args.append('Write_Class=>wc' if label=='dut' else 'Write_Class=>Classify_Write(IR)')
 s+=f'{label}:entity work.{entity} generic map(Mode=>PROFILE_MODE) port map('+','.join(args)+');\n'
s+='''process
variable p : std_logic_vector(7 downto 0);
variable checks : integer := 0;
begin
for opcode in 0 to 255 loop
 for iset_n in 0 to 3 loop
  for mc in 0 to 7 loop
   for profile in 0 to 255 loop
    IR<=std_logic_vector(to_unsigned(opcode,8));ISet<=std_logic_vector(to_unsigned(iset_n,2));
    MCycle<=std_logic_vector(to_unsigned(mc,3));p:=std_logic_vector(to_unsigned(profile,8));
    Ext_Active<=p(0);Data_Long<=p(1);Stream_Long<=p(2);ADL_Mode<=p(3);Has_Width<=p(4);
    Branch_Condition<=p(5);IntCycle<=p(6);NMICycle<=p(7);
    F<=std_logic_vector(to_unsigned((opcode+profile) mod 256,8));
    XY_State<=std_logic_vector(to_unsigned((opcode+mc+profile) mod 4,2));
    Interrupt_Mode<=std_logic_vector(to_unsigned((profile/4) mod 4,2));
    wait for 1 ns;
'''
s+="if not (PROFILE_MODE=0 and iset_n=0 and p(0)='1' and p(4)='1' and p(6)='0' and p(7)='0' and ((((opcode=205) or ((opcode/64)=3 and opcode mod 8=4)) and p(1)=p(3)) or (((opcode=201) or ((opcode/64)=3 and opcode mod 8=0)) and p(1)='1'))) then\n"
for n,_,t in outputs:s+=f'''assert new_{n}=old_{n} report "decoder mismatch {n} mode="&integer'image(PROFILE_MODE)&" op="&integer'image(opcode)&" iset="&integer'image(iset_n)&" MC="&integer'image(mc)&" profile="&integer'image(profile) severity failure;\n'''
s+='''end if;checks:=checks+1;
   end loop;
  end loop;
 end loop;
end loop;
report "PASS Write decoder equivalence checks="&integer'image(checks) severity note;
wait;
end process;
end;
'''
(w/'tb.vhd').write_text(s)
g=os.environ.get('GHDL','ghdl')
for p in [r/'fpga/G80A_eZ80/t80_pack_ez80.vhd',w/'reference.vhd',r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd',w/'tb.vhd']:
 p=subprocess.run([g,'-a','--std=08','-fsynopsys',str(p)],cwd=w,text=True,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
rows=[]
for mode,fault in [(i,False) for i in range(4)]+[(0,True)]:
 p=subprocess.run([g,'-r','--std=08','-fsynopsys','tb_write_r14',f'-gPROFILE_MODE={mode}',f'-gFAULT={str(fault).lower()}','--assert-level=error'],cwd=w,text=True,capture_output=True,timeout=1800);out=p.stdout+p.stderr
 (w/f'm{mode}_f{int(fault)}.log').write_text(out)
 if fault:assert p.returncode!=0 and 'decoder mismatch Write' in out,out
 else:assert p.returncode==0 and 'checks=2097152' in out,out
 rows.append((mode,fault));print('PASS Write decoder differential',mode,fault,flush=True)
(r/'verification_write_r14_result.json').write_text(json.dumps(dict(fresh_runs=4,expected_failure_runs=1,checks_per_positive_run=2097152,total_input_combinations=8388608,legacy_equivalence_combinations=8387456,new_mixed_CALL_RET_combinations_excluded_from_legacy_comparison=1152,all_decoder_outputs_compared=len(outputs),opcode_values=256,ISet_values=4,MCycle_values=8,extension_width_ADL_suffix_branch_IRQ_NMI_profiles=256,Mode_values=[0,1,2,3],flags_and_XY_and_IM_varied_not_independently_exhaustive=True,baseline='R13.1 saved source',sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
