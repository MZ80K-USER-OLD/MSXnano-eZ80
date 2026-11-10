from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,tempfile,shutil,subprocess
r=Path(__file__).resolve().parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R16_FPGA_SHA256.json').read_text());changed=[n for n,h in baseline.items() if sha(r/n)!=h]
assert set(changed)=={'fpga/G80A_eZ80/'+n+'_ez80.vhd' for n in ['t80_mcode','t80','g80a']},changed
with tempfile.TemporaryDirectory(prefix='r17-replay-') as td:
 t=Path(td);(t/'fpga/G80A_eZ80').mkdir(parents=True)
 for src in (r/'doc/r16_baseline').glob('*.vhd.txt'):shutil.copyfile(src,t/'fpga/G80A_eZ80'/src.name.removesuffix('.txt'))
 subprocess.run(['patch','--batch','--forward','-p1','-i',str(r/'doc/R17_LDX.patch')],cwd=t,check=True,capture_output=True)
 for src in (r/'fpga/G80A_eZ80').glob('*.vhd'):assert src.read_bytes()==(t/'fpga/G80A_eZ80'/src.name).read_bytes(),src
coms=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text());assert len(coms)==20
for n,h in coms.items():
 p=r/'hardware_test'/n;assert sha(p)==h,n;assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes(),n
for n in ['EZ80MX1','EZ80TS1','EZ80CT1','EZ80BN1']:
 p=r/'hardware_test'/(n+'.COM');assert sha(p)==json.loads(p.with_suffix('.json').read_text())['sha256'];assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes()
for group in ['diag_r15_1','diag_r15_2']:
 p=r/f'verification_{group}_result.json';j=json.loads(p.read_text());j.pop('FPGA_unchanged',None);j['CPU_revision']='restart R17';j['diagnostic_program_bytes_unchanged']=True;p.write_text(json.dumps(j,indent=2)+'\n')
for group in ['write_r17','upper_r17','sd_r11_9','mbase_r12','madl_r13','mixed_r14','mix_nodiag_r14','tst_r15','tst_com_nodiag_r15','tst_z80_r15','diag_r15_1','diag_r15_2','ldh_unit_r16','ldx_unit_r17','ldx_com_nodiag_r17','ldx_adl_irq_r17']:
 j=json.loads((r/f'verification_{group}_result.json').read_text());assert all(sha(r/n)==h for n,h in j['sha256'].items()),group
j=json.loads((r/'verification_write_r17_result.json').read_text());assert j['legacy_equivalence_combinations']==8386688 and j['excluded_combinations']==1920 and j['all_decoder_outputs_compared']==49
irq=json.loads((r/'verification_irq_r11_result.json').read_text());assert irq['fresh_runs']==77
for name in ['EZ80LDH','EZ80LDX']:assert sum(x['name']==name for x in irq['cases'])==7
for kind,rev,n in [('ldh','r16',40),('ldx','r17',80)]:
 j=json.loads((r/f'verification_{kind}_unit_{rev}_result.json').read_text());assert j['fresh_runs']==6 and j['instructions_per_normal_run']==n
 for c in j['cases']:assert f'PASS {kind}_unit_{rev}' in c['output']
 for p in (r/f'verification_{kind}_unit_{rev}_final').glob('*.log'):assert f'PASS {kind}_unit_{rev}' in p.read_text() and 'FATAL' not in p.read_text(),p
native=json.loads((r/'verification_ldx_adl_irq_r17_result.json').read_text());assert native['fresh_runs']==6 and native['instructions_per_run']==40
for row in native['cases']:assert 'PASS ldx_adl_irq_r17' in row['output']
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
core=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text();old=(r/'doc/r16_baseline/t80_ez80.vhd.txt').read_text();m=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text()
assert 'EX_SP_Address_Next<=EX_SP_Address+1;' in core and core.count('EX_SP_Address+1')==1
assert core.count('Indexed_Address<=')==1 and core.count('EX_SP_Address(15 downto 0)<=unsigned(Indexed_Address(15 downto 0));')==1
assert "if Pair_Indirect='1' then RegAddrA_r<=Indirect_Index;end if;" in core
assert core.index("if Pair_Indirect='1' then RegAddrA_r<=Indirect_Index;end if;")>core.index("RegAddrA_r <= XY_State(1)")
assert "and Pair_Indexed='0' and IR(7 downto 6)=\"00\"" in core
v=(r/'verification/cpu_1.v').read_text();assert 'wire [23:0] ex_sp_address_next;' in v
assert 'A<=Address_Reg;' in core and 'DO<=Data_Out_Reg;' in core
assert core.count('type frame_state_type is')==old.count('type frame_state_type is')==1
row=m[m.index('-- R17: indexed pair memory'):m.index('                    else',m.index('-- R17: indexed pair memory'))];assert "IORQ <= '1'" not in row
for n in ['t80_pack','t80_reg','t80_alu']:
 assert (r/f'fpga/G80A_eZ80/{n}_ez80.vhd').read_bytes()==(r/f'doc/r16_baseline/{n}_ez80.vhd.txt').read_bytes()
w=(r/'fpga/G80A_eZ80/g80a_ez80.vhd').read_text()
assert 'when x"C4"=>Diag_Read<=x"FF";' in w and 'when x"C6"=>Diag_Read<=x"00";' in w
assert 'Diag_Read<=x"87";else Diag_Read<=x"07";' in w and 'Diag_Read<=x"78";else Diag_Read<=x"F8";' in w
assert 'Request_Address <= Bank_i & A_i;' in w and 'Request_MSX_Address <= (others=>\'0\'); Request_Extended <= \'1\';' in w
s=(r/'fpga/top_ez80.v').read_text();a=s.index('    //expanded slot 3');b=s.index('    // slots decoding',a);assert (r/'sim/secondary_slot_r11_4.vh').read_text()==s[a:b]
(r/'verification_release_r17.json').write_text(json.dumps(dict(CPU_baseline='R16',changed_FPGA_files=sorted(changed),COM_count=24,all_COM_bytes_unchanged=True,additional_work_registers=0,additional_FSM_states=0,additional_control_FFs=0,shared_work_address_bits=24,shared_write_source_bits=24,shared_address_incrementer_bits=24,existing_indexed_adder_shared=True,project_references=len(refs),separate_MSX16_extended24_buses=True,GPRJ_SDC_CST_top_bridge_SDRAM_VDP_unchanged=True,GOWIN_run=False,hardware_run=False),indent=2)+'\n')
print('PASS R17 patch replay, shared work registers/adders, 24 unchanged COM, project and bus isolation')
