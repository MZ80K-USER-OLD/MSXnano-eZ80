from pathlib import Path
import subprocess,os,re
r=Path(__file__).resolve().parent.parent;w=r/'verification';w.mkdir(exist_ok=True);g=os.environ.get('GHDL','ghdl')
for n in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
 subprocess.run([g,'-a','--std=08','-fsynopsys',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=w,check=True)
for ext,diag,name in [(True,False,'cpu_1'),(False,False,'cpu_0'),(True,True,'cpu_diag')]:
 p=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches','-gDATA_EXTENDED='+str(ext).lower(),'-gDIAGNOSTICS='+str(diag).lower(),'G80A_eZ80'],cwd=w,text=True,capture_output=True);assert p.returncode==0,p.stderr
 s=re.sub(r'\bdo\b','data_out',p.stdout);needle='  wire [7:0] alu_q;'
 if s.count(needle)==2:
  j=s.index(needle,s.index(needle)+1);s=s[:j]+s[j:].replace(needle,'  wire [7:0] alu_port_q;',1)
  names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1
  s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
 pth=w/(name+'.v');tmp=pth.with_suffix('.tmp');tmp.write_text(s);tmp.replace(pth);(w/(name+'_conversion.log')).write_text(p.stderr)
print('PASS three timing CPU profiles converted')
