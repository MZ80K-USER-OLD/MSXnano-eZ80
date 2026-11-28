"""Prove the release changes only R33's frame-header format guard/interface."""
from pathlib import Path
import hashlib,json,re,subprocess,os,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];W=R/'verification_scope_r36';W.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((R/'doc/R36_BASELINE_R33_SHA256.json').read_text());current={str(p.relative_to(R)):sha(p) for p in (R/'fpga').rglob('*') if p.is_file()}
assert set(current)==set(base)
changed=sorted(p for p in base if base[p]!=current[p]);assert changed==['fpga/G80A_eZ80/g80a_ez80.vhd','fpga/G80A_eZ80/t80_ez80.vhd','fpga/G80A_eZ80/t80_pack_ez80.vhd']
for p in (R/'sim/reference_r33').glob('*.vhd'):assert sha(p)==base['fpga/G80A_eZ80/'+p.name]
assert len(list((R/'sim/reference_r33').glob('*.vhd')))==6
for name in ['t80_ez80.vhd','t80_pack_ez80.vhd']:
 old=(R/'sim/reference_r33'/name).read_text();s=old
 s=s.replace('        Flag_S      : integer := 7;\n        INPUT_FRAME_PREDECODE : boolean := false','        Flag_S      : integer := 7')
 s=s.replace('        Stop        : out std_logic;\n        DI_FRAME_VALID : in std_logic -- sampled alongside DI when predecode enabled','        Stop        : out std_logic')
 if name=='t80_ez80.vhd':
  s=s.replace('    signal Frame_Byte_Valid : std_logic;\n','')
  s=s.replace("                            elsif Frame_Byte_Valid='1' then","                            else\n                                -- R36: only the saved bit 0 selects the restored ADL mode.")
  s=s.replace("                            else Frame_State<=frame_fault;Frame_TS<=to_unsigned(3,3);end if;","                            end if;")
  a=s.index('    -- R29: compare bits 7:1 before the wrapper input FF; bit 0 remains mode data.');b=s.index('    HALT_n',a);s=s[:a]+s[b:]
 assert s==(R/'fpga/G80A_eZ80'/name).read_text(),name+' changed beyond permitted scope'
old=(R/'sim/reference_r33/g80a_ez80.vhd').read_text();s=old
for line in ['    signal DI_Frame_Valid_Reg : std_logic; -- R29: same capture/hold as DI_Reg\n','            INPUT_FRAME_PREDECODE => true,\n','            DI_FRAME_VALID => DI_Frame_Valid_Reg,\n',"                    if Input_Byte(7 downto 1)=\"0000001\" then DI_Frame_Valid_Reg<='1';\n                    else DI_Frame_Valid_Reg<='0';end if;\n"]:
 assert s.count(line)==1;s=s.replace(line,'')
wrapper=(R/'fpga/G80A_eZ80/g80a_ez80.vhd').read_text();assert s==wrapper,'wrapper capture/WAIT/bus behavior changed'
core=(R/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
for token in ['INPUT_FRAME_PREDECODE','DI_FRAME_VALID','Frame_Byte_Valid','Input_Byte_Reg','DI_CAPTURE_ENABLE']:
 assert token not in core and token not in wrapper,token
assert "Data_Out_Reg<=\"0000001\" & Frame_Mode_Bit" in core
# Current and reference capture predicates/WAIT behavior are preserved by exact scope above.
models=[]
for model in ['cpu_1.v','cpu_diag.v','cpu_0.v']:
 txt=(R/'verification'/model).read_text();mods=re.findall(r'module\s+(\w+)\s*\((.*?)endmodule',txt,re.S)
 top=next(b for n,b in mods if n=='G80A_eZ80');a=dict(re.findall(r'assign\s+(\w+)\s*=\s*(.*?);',top))
 q=a['di_reg'];assert re.fullmatch(r'n\d+_q',q) and re.search(r'reg \[7:0\] '+q+r';',top)
 edge=re.search(r'always @\(negedge CLK_n\)\s*'+q+r'\s*<=\s*(\w+)\s*;',top);assert edge
 assert a[edge[1]].endswith(' : di_reg')
 assert '.di(di_reg)' in top
 assert all('di_frame_valid' not in b.lower() and 'input_byte_reg' not in b.lower() for n,b in mods)
 models.append(dict(model=model,capture_module='G80A_eZ80',bits=8,edge='falling',hold_mux=True,format_tag_absent=True))
coms=[]
for manifest in ['R26_COM_MANIFEST.json','R29_1_DIAGNOSTIC_COM_MANIFEST.json']:
 for row in json.loads((R/'doc'/manifest).read_text()):
  n=row['name'] if row['name'].endswith('.COM') else row['name']+'.COM';assert sha(R/n)==row['sha256']==sha(R/'hardware_test'/n);coms.append(n)
assert len(set(coms))==len(coms)==30
baseline_tests=json.loads((R/'doc/R32_TEST_BASELINE_SHA256.json').read_text());assert all(sha(R/p)==h for p,h in baseline_tests.items())
for p in [R/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',R/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 refs=E.parse(p).findall('.//File');assert len(refs)==123 and all((p.parent/f.get('path')).is_file() for f in refs)
w=W/'vhdl93';w.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 a=subprocess.run([os.environ['GHDL'],'-a','--std=93','-fsynopsys','-fexplicit',str(R/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=w,capture_output=True,text=True);assert not a.returncode,a.stderr
models_sha=json.loads((R/'verification/r36_rtl_sha256.json').read_text());assert all(sha(R/p)==h for p,h in models_sha.items())
result=dict(changed=changed,FPGA_files=len(current),scope='R33 format predicate and interface removal only',wrapper_capture_and_WAIT_preserved=True,decoder_ALU_registers_memory_bridge_and_constraints_unchanged=True,mode_header_push_02_03_unchanged=True,COMs_unchanged=30,GPRJ_refs_each=123,VHDL93=True,GHDL_models=models,FPGA_sha256=current)
(W/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS R36 exact R33 scope, wrapper 8-bit capture, 30 COM unchanged, both GPRJs, VHDL93')
