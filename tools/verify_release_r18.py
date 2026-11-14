from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,tempfile,shutil,subprocess,re
r=Path(__file__).resolve().parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((r/'doc/R17_FPGA_SHA256.json').read_text());current={str(p.relative_to(r)) for p in (r/'fpga').rglob('*') if p.is_file()}
assert current==set(baseline), 'unexpected FPGA file addition/deletion'
changed=[n for n,h in baseline.items() if sha(r/n)!=h]
assert set(changed)=={'fpga/G80A_eZ80/'+n+'_ez80.vhd' for n in ['t80','g80a']},changed
with tempfile.TemporaryDirectory(prefix='r18-replay-') as td:
 t=Path(td);(t/'fpga/G80A_eZ80').mkdir(parents=True)
 for src in (r/'doc/r17_baseline').glob('*.vhd.txt'):shutil.copyfile(src,t/'fpga/G80A_eZ80'/src.name.removesuffix('.txt'))
 subprocess.run(['patch','--batch','--forward','-p1','-i',str(r/'doc/R18_RST.patch')],cwd=t,check=True,capture_output=True)
 for src in (r/'fpga/G80A_eZ80').glob('*.vhd'):assert src.read_bytes()==(t/'fpga/G80A_eZ80'/src.name).read_bytes(),src
old_coms=json.loads((r/'doc/R17_COM_SHA256.json').read_text());assert len(old_coms)==24
for n,h in old_coms.items():assert sha(r/'hardware_test'/n)==h,n
coms=json.loads((r/'doc/PRELOADED_COM_SHA256.json').read_text());assert len(coms)==20
for n,h in coms.items():assert sha(r/'hardware_test'/n)==h,n
for n in ['EZ80MX1','EZ80TS1','EZ80CT1','EZ80BN1','EZ80RS8']:
 p=r/'hardware_test'/(n+'.COM');assert sha(p)==json.loads(p.with_suffix('.json').read_text())['sha256']
for p in (r/'hardware_test').glob('*.COM'):assert bytes.fromhex(p.with_suffix('.hex').read_text())==p.read_bytes(),p
assert len(list((r/'hardware_test').glob('*.COM')))==25
for group in ['diag_r15_1','diag_r15_2']:
 p=r/f'verification_{group}_result.json';j=json.loads(p.read_text());j.pop('FPGA_unchanged',None);j['CPU_revision']='restart R18';j['diagnostic_program_bytes_unchanged']=True;p.write_text(json.dumps(j,indent=2)+'\n')
for group in ['write_r18','upper_r18','sd_r11_9','mbase_r12','madl_r13','mixed_r14','mix_nodiag_r14','tst_r15','tst_com_nodiag_r15','tst_z80_r15','diag_r15_1','diag_r15_2','ldh_unit_r16','ldx_unit_r17','ldx_com_nodiag_r17','ldx_adl_irq_r17','rst_r18','rst_interrupt_r18','rst_com_r18']:
 j=json.loads((r/f'verification_{group}_result.json').read_text());assert all(sha(r/n)==h for n,h in j['sha256'].items()),group
j=json.loads((r/'verification_write_r18_result.json').read_text());assert j['legacy_equivalence_combinations']==8388608 and j['excluded_combinations']==0 and j['all_decoder_outputs_compared']==49
irq=json.loads((r/'verification_irq_r11_result.json').read_text());assert irq['fresh_runs']==77
native=json.loads((r/'verification_ldx_adl_irq_r17_result.json').read_text());assert native['fresh_runs']==6
for group,n in [('rst_r18',312),('rst_interrupt_r18',24),('rst_com_r18',9)]:assert json.loads((r/f'verification_{group}_result.json').read_text())['fresh_runs']==n
# Assert actual stress coverage, not just a passing status string.
for group,ids in [('rst_r18',range(96)),('rst_interrupt_r18',range(104,112))]:
 rows=json.loads((r/f'verification_{group}_result.json').read_text())['cases']
 for c in ids:
  stats=[]
  for row in rows:
   if row['case'][0]==c and row['case'][2] and not row['case'][4]:
    match=re.search(r'frame_WAIT=(\d+) pause=(\d+) bus_grant=(\d+)',row['result']);assert match,(group,row)
    stats.append(tuple(map(int,match.groups())))
  assert len(stats)==2 and any(x[0]>0 for x in stats) and all(x[1]>0 and x[2]==1 for x in stats),(group,c,stats)
hw=json.loads((r/'verification_rst_com_r18_result.json').read_text());assert hw['COM_sha256']==sha(r/'hardware_test/EZ80RS8.COM')
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';refs=ET.parse(p).findall('.//File')
for f in refs:assert (p.parent/f.attrib['path']).is_file(),f.attrib
core=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text();old=(r/'doc/r17_baseline/t80_ez80.vhd.txt').read_text()
# Existing state/register declarations remain identical apart from three combinational selectors.
olddecl=old[old.index('    type frame_state_type is'):old.index('    function PC_Width')]
newdecl=core[core.index('    type frame_state_type is'):core.index('    function PC_Width')]
newdecl=newdecl.replace('    signal Frame_Rst, Frame_Rst_Ready, Frame_Destination_Long : std_logic;\n','')
assert olddecl==newdecl,'unexpected state/register declaration change'
assert "Ctrl_Target<=x\"0000\" & \"00\" & IR(5 downto 3) & \"000\";" in core
assert "Frame_Is_Call<='1';Frame_Mode_Bit<=ADL_Mode;Ctrl_Return<=std_logic_vector(PC);" in core
assert core.count('Frame_Stack_Next<=Frame_Stack_Value+Frame_Stack_Delta;')==1
assert 'A<=Address_Reg;' in core and 'DO<=Data_Out_Reg;' in core
w=(r/'fpga/G80A_eZ80/g80a_ez80.vhd').read_text()
assert 'Diag_Read<=x"8F";else Diag_Read<=x"0F";' in w and 'Diag_Read<=x"70";else Diag_Read<=x"F0";' in w
assert 'Request_Address <= Bank_i & A_i;' in w and 'Request_MSX_Address <= (others=>\'0\'); Request_Extended <= \'1\';' in w
s=(r/'fpga/top_ez80.v').read_text();a=s.index('    //expanded slot 3');b=s.index('    // slots decoding',a);assert (r/'sim/secondary_slot_r11_4.vh').read_text()==s[a:b]
(r/'verification_release_r18.json').write_text(json.dumps(dict(CPU_baseline='R17',changed_FPGA_files=sorted(changed),original_24_COM_unchanged=True,new_COM='EZ80RS8.COM',COM_count=25,additional_work_registers=0,additional_FSM_states=0,additional_control_FFs=0,additional_combinational_selectors=3,shared_frame_engine=True,shared_stack_incrementer_bits=24,project_references=len(refs),separate_MSX16_extended24_buses=True,GPRJ_SDC_CST_top_bridge_SDRAM_VDP_unchanged=True,GOWIN_run=False,hardware_run=False),indent=2)+'\n')
print('PASS R18 release: R17 patch replay, two FPGA files, shared frame states/registers/adder, 24 unchanged COM + EZ80RS8, project/bus isolation')
