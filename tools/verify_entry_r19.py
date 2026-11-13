from pathlib import Path
import os, subprocess, re
r=Path(__file__).resolve().parent.parent
w=r/'verification';w.mkdir(exist_ok=True)
g=os.environ['GHDL']
for n in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
 subprocess.run([g,'-a','--std=08','-fsynopsys',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=w,check=True)
for ext,diag,name in [(True,False,'cpu_1.v'),(False,False,'cpu_0.v'),(True,True,'cpu_diag.v')]:
 a=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches',f'-gDATA_EXTENDED={str(ext).lower()}',f'-gDIAGNOSTICS={str(diag).lower()}','G80A_eZ80'],cwd=w,text=True,capture_output=True)
 assert a.returncode==0,a.stderr
 s=re.sub(r'\bdo\b','data_out',a.stdout);needle='  wire [7:0] alu_q;'
 if s.count(needle)==2:
  j=s.index(needle,s.index(needle)+1);s=s[:j]+s[j:].replace(needle,'  wire [7:0] alu_port_q;',1)
  names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1
  s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
 # Simulation-only invariant: the registered request must equal the old R18
 # combinational RST start condition at every accepted fetch T4.
 needle='  assign frame_rst = '
 i=s.index(needle);module_end=s.index('endmodule',i)
 monitor="""
  always @(posedge clk_n) begin
    if (reset_n && cen && !busack && !frame_active && mcycle == 3'b001 && tstate == 3'd4 && extensions_enabled)
      if (frame_rst_pending !== (frame_rst_ready | frame_unsupported | irq_im0))
        $fatal(1, "R19 registered frame request differs at accepted fetch T4");
  end
"""
 s=s[:module_end]+monitor+s[module_end:]
 (w/name).write_text(s);(w/(name+'.conversion.log')).write_text(a.stderr)
 print('PASS converted and entry invariant installed:',name,flush=True)
