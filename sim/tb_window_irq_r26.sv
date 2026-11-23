`timescale 1ns/1ps
// CPU/window functional test with separate MSX and extended RAM arrays.
// Physical SDRAM mapping is covered by the actual COM/SDRAM suite.
module tb_window_irq_r26;
 parameter NMI=0,STRESS=0,LOCK=0;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer tick=0,div=0;reg run=1;
 always @(posedge clk)begin
  tick<=tick+1;
  if(!reset_n)begin div<=0;run<=1;end
  else if(div==3)begin div<=0;run<=!STRESS||tick%257<180;end else div<=div+1;
 end
 wire ce=div==0&&run,cf=div==2&&run,wait_n=!STRESS||tick%113<70;
 reg [7:0] lowmem[0:65535],mem[0:1048575];
 wire [23:0] a;wire [15:0] msx;wire ew,mr,io,rd,wr,rf,m1,halt_n;wire [7:0] dout;
 reg irq=0,nmi=0,fired=0;integer pulse=0,vector_reads=0,stack_writes=0,i;
 wire [7:0] din=!io?8'hfe:!mr&&!rd?(ew?mem[a[19:0]]:lowmem[msx]):8'hff;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(reset_n),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(1'b1),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ew),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(halt_n),.DO(dout));
 always @(posedge clk)if(reset_n)begin
  if(!mr&&!wr)begin
   if(ew)begin mem[a[19:0]]<=dout;if(a>=24'h057ffd&&a<=24'h057fff)stack_writes=stack_writes+1;end
   else begin if(msx<128||msx==16'hffff)$fatal(1,"MSX vector/slot write %h",msx);lowmem[msx]<=dout;end
  end
  if(ce)begin
   if(!halt_n&&!fired)begin fired<=1;if(NMI)begin nmi<=1;pulse<=8;end else irq<=1;end
   if(pulse>0)begin pulse<=pulse-1;if(pulse==1)nmi<=0;end
   if(!io&&!m1)irq<=0;
   if(!mr&&!rd&&(a==24'h000038||a==24'h000066))begin
    if(!ew||msx!==0)$fatal(1,"native vector reached MSX");vector_reads=vector_reads+1;
   end
   if(cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n&&a==(LOCK?24'h000300:24'h000200))begin
    if(!fired||vector_reads==0||stack_writes==0||mem[20'ha9200]!== (NMI?8'h66:8'h77))$fatal(1,"IRQ coverage/result");
    if(cpu.u0.spl!==24'h058000||cpu.u0.sp!==16'hf000||cpu.u0.adl_mode!==0||cpu.u0.mbase!==0)$fatal(1,"IRQ cleanup");
    if(lowmem[16'hffff]!==8'h5c||lowmem[16'h38]!==8'hc7||lowmem[16'h66]!==8'hc7)$fatal(1,"MSX state changed");
    $display("PASS window_irq R26 NMI=%0d stress=%0d lock=%0d vector_reads=%0d",NMI,STRESS,LOCK,vector_reads);$finish;
   end
  end
 end
 task putlow(input integer a0,input [255:0] bytes,input integer n);integer j;begin for(j=0;j<n;j=j+1)lowmem[a0+j]=bytes[j*8+:8];end endtask
 initial begin
  for(i=0;i<65536;i=i+1)lowmem[i]=0;
  // DI; SP=F000; unlock; JP.LIL 0A8000.
  putlow(0,256'h0a8000c35b79ed5a3e79eda53ee7e701f00031f3,20);
  mem[20'ha8000]=8'h31;mem[20'ha8001]=0;mem[20'ha8002]=8'h80;mem[20'ha8003]=5;
  mem[20'ha8004]=8'h3e;mem[20'ha8005]=8'hff;mem[20'ha8006]=8'hed;mem[20'ha8007]=8'h6d;
  mem[20'ha8008]=8'hed;mem[20'ha8009]=8'h56;mem[20'ha800a]=8'hfb;mem[20'ha800b]=0;mem[20'ha800c]=8'h76;
  mem[20'ha800d]=8'hf3;mem[20'ha800e]=8'h3e;mem[20'ha800f]=LOCK?8'hff:0;mem[20'ha8010]=8'hed;mem[20'ha8011]=8'h6d;
  mem[20'ha8012]=8'h40;mem[20'ha8013]=8'hc3;mem[20'ha8014]=0;mem[20'ha8015]=2;
  mem[20'h38]=8'hc3;mem[20'h39]=0;mem[20'h3a]=8'h90;mem[20'h3b]=8'h0a;
  mem[20'h66]=8'hc3;mem[20'h67]=0;mem[20'h68]=8'h91;mem[20'h69]=8'h0a;
  mem[20'ha9000]=8'h3e;mem[20'ha9001]=8'h77;mem[20'ha9002]=8'h32;mem[20'ha9003]=0;mem[20'ha9004]=8'h92;mem[20'ha9005]=8'h0a;mem[20'ha9006]=8'hed;mem[20'ha9007]=8'h4d;
  mem[20'ha9100]=8'h3e;mem[20'ha9101]=8'h66;mem[20'ha9102]=8'h32;mem[20'ha9103]=0;mem[20'ha9104]=8'h92;mem[20'ha9105]=8'h0a;mem[20'ha9106]=8'hed;mem[20'ha9107]=8'h45;
  if(LOCK)putlow(16'h200,256'h0300c30079ed003ee7e701,11);
  lowmem[16'h38]=8'hc7;lowmem[16'h66]=8'hc7;lowmem[16'hffff]=8'h5c;
  repeat(12)@(negedge clk);reset_n=1;
 end
 initial begin #10000000;$fatal(1,"timeout a=%h pc=%h IR=%h MB=%h",a,cpu.u0.pc,cpu.u0.ir,cpu.u0.mbase);end
endmodule
