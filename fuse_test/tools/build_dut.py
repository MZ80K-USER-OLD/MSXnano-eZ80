"""Build unchanged R37 through GHDL; generate simulation-only architectural state deposits."""
from pathlib import Path
import os,subprocess,re,hashlib,json,shutil
R=Path(__file__).resolve().parents[1];RTL=R.parent/'fpga/G80A_eZ80';B=R/'build';B.mkdir(exist_ok=True);g=os.environ.get('GHDL',shutil.which('ghdl') or 'ghdl')
for name in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 a=subprocess.run([g,'-a','--std=08','-fsynopsys',str(RTL/(name+'_ez80.vhd'))],cwd=B,capture_output=True,text=True);assert not a.returncode,a.stderr
a=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches','-gDATA_EXTENDED=true','-gDIAGNOSTICS=false','G80A_eZ80'],cwd=B,capture_output=True,text=True);assert not a.returncode,a.stderr
s=re.sub(r'\bdo\b','data_out',a.stdout);needle='  wire [7:0] alu_q;'
if s.count(needle)==2:
 p=s.index(needle,s.index(needle)+1);s=s[:p]+s[p:].replace(needle,'  wire [7:0] alu_port_q;',1);names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1
 s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
(B/'dut.v').write_text(s)
mods=dict(re.findall(r'module\s+(\w+)\s*\((.*?)endmodule',s,re.S));core=next(b for n,b in mods.items() if n.startswith('t80_ez80_'))
def aliases(body):return dict(re.findall(r'assign\s+(\w+)\s*=\s*(.*?);',body))
a=aliases(core);ra=aliases(mods['t80_reg_ez80']);ta=aliases(mods['G80A_eZ80'])
assigns={'acc':'st[0][15:8]','f':'st[0][7:0]','ap':'st[4][15:8]','fp':'st[4][7:0]','spl':'st[10]','pc':'st[11]','address_reg':'st[11][15:0]','address_bank_reg':"st[18] ? st[11][23:16] : st[19][7:0]",'i':'st[12][7:0]','i_upper':'st[12][15:8]','r':'st[13][7:0]','inte_ff1':'st[14][0]','inte_ff2':'st[15][0]','istatus':'st[16][1:0]','halt_ff':'st[17][0]','adl_mode':'st[18][0]','mbase':'st[19][7:0]','madl':'st[20][0]','sp':'st[21][15:0]','extensions_enabled':"1'b1",'data_long':'st[18][0]','stream_long':'st[18][0]','tstate':"3'd1"}
lines=[]
for k,v in assigns.items():
 q=a[k];assert re.fullmatch(r'n\d+_q',q),(k,q);lines.append(f'cpu.u0.{q} = {v};')
q=ta['di_reg'];assert re.fullmatch(r'n\d+_q',q);lines.append(f'cpu.{q} = 0;')
idx=[1,2,3,8,5,6,7,9]
for i,si in enumerate(idx):lines += [f'cpu.u0.regs.regsh[{i}]=st[{si}][15:8];',f'cpu.u0.regs.regsl[{i}]=st[{si}][7:0];']
q=ra['regsu'];assert re.fullmatch(r'n\d+_q',q);lines.append(f'cpu.u0.regs.{q} = '+'{'+','.join(f'st[{si}][23:16]' for si in idx)+'};')
(B/'init_state.vh').write_text('\n'.join(lines)+'\n')
(B/'event_inject.vh').write_text(f'''if(ev==1)begin nmi_pin=1;cpu.u0.{a['nmi_s']}=1;end
if(ev==2)begin int_pin=0;cpu.u0.{a['int_s']}=1;end
''')
(B/'event_start.vh').write_text(f'''cpu.u0.{a['tstate']}=3'd4;
cpu.u0.{a['mcycles']}=3'd1;
''')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=json.loads((R/'doc/R37_RTL_SHA256.json').read_text());assert expected=={p.name:sha(p) for p in (RTL).glob('*.vhd')},'R37 source changed'
version=subprocess.run([g,'--version'],capture_output=True,text=True,check=True).stdout
(B/'BUILD.json').write_text(json.dumps(dict(GHDL=version,RTL_sha256=expected,dut_sha256=sha(B/'dut.v'),state_mapping_sha256=sha(B/'init_state.vh'),state_deposits='simulation only; checked roundtrip for all 22 fields before each case',FPGA_source_changed=False),indent=2)+'\n')
print('PASS built R37 and generated state mapping')
