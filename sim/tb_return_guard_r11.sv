`timescale 1ns/1ps
module tb_return_guard_r11;
 parameter ADL=1,SUFFIX=73,OP=69,ALIAS=0;
 reg clk=0,rst=0;always #10 clk=~clk;reg [3:0] div=0;integer ticks=0;
 always @(posedge clk)begin ticks<=ticks+1;div<=div+1;end
 wire ce=div==0,cf=div==8,wait_n=ticks%113<70;
 wire [23:0] a;wire mr,io,rf,rd,wr,m1,halt_n;wire [7:0] dout;reg [7:0] rom[0:65535];integer i;
 wire [7:0] din=!mr&&!rd?rom[a[15:0]]:8'hff;
 G80A_eZ80 cpu(.RESET_n(rst),.CLK_n(clk),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),.A24(a),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
 always @(posedge clk)if(rst)begin
  if(!mr&&!wr)$fatal(1,"unsupported frame touched memory");
  if(!halt_n)begin
   if(cpu.u0.adl_mode!==ADL||cpu.u0.sp!==16'hf000||cpu.u0.spl!==24'hffffff)$fatal(1,"unsupported return changed SP/mode");
   $display("PASS return_guard_r11 ADL=%d suffix=%h opcode=%h alias=%d",ADL,SUFFIX,OP,ALIAS);$finish;
  end
 end
 initial begin
  for(i=0;i<65536;i=i+1)rom[i]=0;
  {rom[0],rom[1],rom[2]}={8'hc3,8'h00,8'h01};
  {rom[16'h100],rom[16'h101],rom[16'h102],rom[16'h103],rom[16'h104],rom[16'h105],rom[16'h106],rom[16'h107],rom[16'h108],rom[16'h109],rom[16'h10a],rom[16'h10b],rom[16'h10c],rom[16'h10d],rom[16'h10e]}={8'hf3,8'h31,8'h00,8'hf0,8'h01,8'he7,8'he7,8'h3e,8'ha5,8'hed,8'h79,8'h3e,8'h5a,8'hed,8'h79};
  if(ADL)begin {rom[16'h10f],rom[16'h110],rom[16'h111],rom[16'h112],rom[16'h113]}={8'h5b,8'hc3,8'h00,8'h30,8'h01};end
  else begin {rom[16'h10f],rom[16'h110],rom[16'h111]}={8'hc3,8'h00,8'h30};end
  if(ALIAS)begin rom[16'h3000]=8'hed;rom[16'h3001]=8'h75;end
  else begin rom[16'h3000]=SUFFIX;rom[16'h3001]=8'hed;rom[16'h3002]=OP;end
  repeat(12)@(negedge clk);rst=1;
 end
 initial begin #10000000;$fatal(1,"return guard timeout pc=%h",cpu.u0.pc);end
endmodule
