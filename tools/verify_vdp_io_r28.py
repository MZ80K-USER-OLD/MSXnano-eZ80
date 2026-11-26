"""Extract the actual top decode and VDP I/O latch; compare valid bus transactions."""
from pathlib import Path
import re,os,subprocess,json
r=Path(__file__).resolve().parents[1];w=r/'verification_vdp_io_r28';w.mkdir(exist_ok=True)
s=(r/'fpga/top_ez80.v').read_text()
assert 'wire [15:0] cpu_io_addr = cpu_addr24[15:0];' in s
assert '.mode    (cpu_io_addr[1:0])' in s
assigns='\n'.join(re.findall(r'^\s*assign vdp_cs[wr]_n = .*?;',s,re.M));assert assigns.count('cpu_io_addr[7:2]')==2
vdp=(r/'fpga/tn_vdp_v3_v9958/src/v9958_top.v').read_text();a=vdp.index('     always @(posedge clk_w');e=vdp.index('    wire pal_mode;',a);body=vdp[a:e]
head='''module io_latch(input clk_w,reset_n_w,input [1:0] mode,input [7:0] cdo,input csrn_w,cswn_w,output reg CpuReq,output reg CpuWrt,output reg [15:0] CpuAdr,output reg [7:0] CpuDbo);
reg io_state_r=0;reg[1:0]cs_latch;
'''
(w/'io_latch.v').write_text(head+body+'\nendmodule\n')
tb='''`timescale 1ns/1ps
module tb_vdp_io_r28;
reg clk=0,rst=0;always #5 clk=~clk;
reg [23:0] cpu_addr24=0;wire[15:0]cpu_io_addr=cpu_addr24[15:0];
reg ext=0,bus_iorq_n=1,bus_m1_n=1,bus_rd_n=1,bus_wr_n=1;reg[7:0]data=0;
wire[15:0]bus_addr=ext?16'h0000:cpu_addr24[15:0];
wire vdp_csw_n,vdp_csr_n;
'''+assigns+'''
wire oldw=(bus_addr[7:2]==6'b100110&&!bus_iorq_n&&bus_m1_n&&!bus_wr_n)?0:1;
wire oldr=(bus_addr[7:2]==6'b100110&&!bus_iorq_n&&bus_m1_n&&!bus_rd_n)?0:1;
wire nr,nw,orq,ow;wire[15:0]na,oa;wire[7:0]nd,od;
io_latch n(clk,rst,cpu_io_addr[1:0],data,vdp_csr_n,vdp_csw_n,nr,nw,na,nd);
io_latch o(clk,rst,bus_addr[1:0],data,oldr,oldw,orq,ow,oa,od);
integer a,k,j,checks=0,requests=0;
task check;begin #0.01;
 if({vdp_csw_n,vdp_csr_n}!=={oldw,oldr})$fatal(1,"VDP decode mismatch");
 if({nr,nw}!=={orq,ow})$fatal(1,"VDP handshake mismatch");
 if(nr)begin
  if({na,nd}!=={oa,od})$fatal(1,"VDP command payload mismatch");requests=requests+1;
 end
 if(ext&&(nr||!vdp_csw_n||!vdp_csr_n))$fatal(1,"extended memory reached VDP");
 checks=checks+1;
end endtask
initial begin
 repeat(3)@(posedge clk);@(negedge clk);rst=1;
 for(a=0;a<65536;a=a+1)for(k=0;k<8;k=k+1)begin
  @(negedge clk);cpu_addr24={8'h07,a[15:0]};data=a[7:0];
  // ordinary read/write I/O, extended memory, IACK, and MSX memory.
  ext=(k==2||k==5);bus_iorq_n=(k==2||k==4||k==5||k==6||k==7);bus_m1_n=(k!=3&&k!=7);
  bus_rd_n=(k==1||k==5||k==6||k==7);bus_wr_n=(k!=1&&k!=5&&k!=6);
  repeat(3)begin @(posedge clk);check;end
  @(negedge clk);ext=0;bus_iorq_n=1;bus_rd_n=1;bus_wr_n=1;
  repeat(3)begin @(posedge clk);check;end
 end
 if(requests==0)$fatal(1,"no VDP I/O coverage");
 $display("PASS R28 VDP IO checks=%0d requests=%0d",checks,requests);$finish;
end
endmodule
'''
(w/'tb.sv').write_text(tb)
v=w/'run.vvp';p=subprocess.run([os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_vdp_io_r28','-o',str(v),str(w/'tb.sv'),str(w/'io_latch.v')],capture_output=True,text=True);assert not p.returncode,p.stderr
p=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=180);out=p.stdout+p.stderr;(w/'result.log').write_text(out);assert not p.returncode and 'PASS R28 VDP IO'in out,out
(w/'result.json').write_text(json.dumps(dict(addresses=65536,classes=8,actual_top_decode=True,actual_VDP_IO_latch=True,full_VDP=False,output=out),indent=2)+'\n');print(out)
