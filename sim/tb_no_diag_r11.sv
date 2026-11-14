`timescale 1ns/1ps
`include `TEST_HEADER
module tb_no_diag_r11;
 parameter REQUEST=1,EXTENDED=1,STRESS=1;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer ticks=0;reg [3:0] div=0;reg enable_run=1;
 always @(posedge clk)begin
  ticks<=ticks+1;
  if(!reset_n)begin div<=0;enable_run<=1;end
  else begin div<=div+1;if(div==15)enable_run<=!STRESS||ticks%257<180;end
 end
 wire ce=div==0&&enable_run,cf=div==8&&enable_run;
 wire wait_n=!STRESS||ticks%113<70;
 wire [23:0] a;wire mr,io,rf,rd,wr,m1,halt_n;wire [7:0] dout;
 reg [7:0] mem[0:65535];wire [7:0] din=!mr&&!rd?mem[a[15:0]]:8'hff;
 G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(clk),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),.A24(a),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
 integer i,bdos=0,waits=0;reg oldwrite=0,oldbdos=0;integer expected;
 always @(posedge clk)if(reset_n)begin
  if(a[23:16]!=0||cpu.u0.adl_mode!==0)$fatal(1,"diagnostic-dependent feature executed without hook");
  if(!halt_n)$fatal(1,"unsupported opcode reached HALT");
  if(!mr&&!wr)mem[a[15:0]]<=dout;
  if(!wait_n)waits=waits+1;
  if(cpu.u0.extensions_enabled&&cpu.u0.inte_ff1!==0)$fatal(1,"DI lost while extended");
  if(!m1&&!mr&&a==5&&!oldbdos)begin
   if(cpu.u0.extensions_enabled!==0||cpu.u0.inte_ff1!==1)$fatal(1,"BDOS outside restored state");bdos=bdos+1;
  end
  oldbdos<=!m1&&!mr&&a==5;
  if(!io&&!wr&&a[7:0]==8'hf0&&!oldwrite)$write("%c",dout);
  oldwrite<=!io&&!wr&&a[7:0]==8'hf0;
  if(!m1&&!mr&&a==24'h80)begin
   expected=!REQUEST?4:!EXTENDED?3:5;
   if(mem[`P2_STATUS]!==expected||cpu.u0.sp!==16'hf000||cpu.u0.inte_ff1!==1||cpu.u0.extensions_enabled!==0||bdos!=1)$fatal(1,"return/status mismatch %h expected %h SP=%h",mem[`P2_STATUS],expected,cpu.u0.sp);
   if({mem[16'ha1],mem[16'ha0]}!==16'h1357||{mem[16'ha3],mem[16'ha2]}!==16'h2468||mem[16'hffff]!==8'h5c)$fatal(1,"IX/IY/slot changed");
   if(STRESS&&waits==0)$fatal(1,"no WAIT stress");
   $display("PASS R10 guard request=%0d ext=%0d status=%0d WAIT=%0d",REQUEST,EXTENDED,expected,waits);$finish;
  end
 end
 initial begin
  for(i=0;i<65536;i=i+1)mem[i]=0;
  mem[0]=8'hc3;mem[1]=8'h40;mem[2]=0;
  {mem[5],mem[6],mem[7]}={8'hc3,8'h10,8'h00};
  {mem[16'h10],mem[16'h11],mem[16'h12],mem[16'h13],mem[16'h14],mem[16'h15],mem[16'h16],mem[16'h17],mem[16'h18],mem[16'h19],mem[16'h1a],mem[16'h1b]}={8'hfb,8'h00,8'h1a,8'hfe,8'h24,8'hc8,8'hd3,8'hf0,8'h13,8'hc3,8'h10,8'h00};
  {mem[16'h40],mem[16'h41],mem[16'h42],mem[16'h43],mem[16'h44],mem[16'h45],mem[16'h46],mem[16'h47],mem[16'h48],mem[16'h49],mem[16'h4a],mem[16'h4b],mem[16'h4c],mem[16'h4d],mem[16'h4e],mem[16'h4f]}={8'hfb,8'h00,8'h31,8'h00,8'hf0,8'hdd,8'h21,8'h57,8'h13,8'hfd,8'h21,8'h68,8'h24,8'hcd,8'h00,8'h01};
  {mem[16'h50],mem[16'h51],mem[16'h52],mem[16'h53],mem[16'h54],mem[16'h55],mem[16'h56],mem[16'h57],mem[16'h58],mem[16'h59],mem[16'h5a],mem[16'h5b],mem[16'h5c],mem[16'h5d],mem[16'h5e]}={8'hdd,8'he5,8'he1,8'h22,8'ha0,8'h00,8'hfd,8'he5,8'he1,8'h22,8'ha2,8'h00,8'hc3,8'h80,8'h00};
  $readmemh(`TEST_HEX,mem,16'h100,`P2_COM_END);
  mem[16'h80]=REQUEST?5:0;mem[16'h81]=" ";mem[16'h82]="/";mem[16'h83]="R";mem[16'h84]="U";mem[16'h85]="N";mem[16'hffff]=8'h5c;
  repeat(12)@(negedge clk);reset_n=1;
 end
 initial begin #30000000;$fatal(1,"guard timeout pc=%h",cpu.u0.pc);end
endmodule
