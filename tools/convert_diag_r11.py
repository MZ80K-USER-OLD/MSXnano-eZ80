from pathlib import Path
import os,subprocess,re
r=Path(__file__).resolve().parent.parent;w=r/'verification';w.mkdir(exist_ok=True);g=os.environ.get('GHDL','ghdl')
for n in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
 subprocess.run([g,'-a','--std=08','-fsynopsys',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=w,check=True)
p=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches','-gDATA_EXTENDED=true','-gDIAGNOSTICS=true','G80A_eZ80'],cwd=w,text=True,capture_output=True);assert p.returncode==0,p.stderr
s=re.sub(r'\bdo\b','data_out',p.stdout);needle='  wire [7:0] alu_q;'
if s.count(needle)==2:
 j=s.index(needle,s.index(needle)+1);s=s[:j]+s[j:].replace(needle,'  wire [7:0] alu_port_q;',1)
 names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1
 s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
(w/'cpu_diag.v').write_text(s);(w/'conversion_diag.log').write_text(p.stderr);print('PASS diagnostics-enabled CPU conversion (not Gowin)')
