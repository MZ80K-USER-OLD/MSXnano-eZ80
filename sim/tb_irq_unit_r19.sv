`timescale 1ns/1ps
module tb_irq_unit_r19;
 parameter CASE=0,STRESS=0,PHASE=0;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer ticks=0;reg [3:0] div=0;reg enable_run=1;
 always @(posedge clk)begin ticks<=ticks+1;if(!reset_n)begin div<=PHASE;enable_run<=1;end else begin div<=div+1;if(div==15)enable_run<=!STRESS||ticks%257<180;end end
 wire ce=div==0&&enable_run,cf=div==8&&enable_run;
 wire [23:0] a;wire mr,io,rf,rd,wr,m1,halt_n;wire [7:0] dout;
 reg [7:0] mem[0:16777215];reg irq=0,nmi=0,triggered=0,second_nmi=0;integer pulse=0,forced=0,entries=0,nmis=0,acks=0,writes=0,waits=0;reg old_entry=0,old_write=0,hold_valid=0;reg [80:0] held,now_state;
 wire first_transfer=CASE<2&&!mr&&!wr&&a==24'h07ffff;
 wire wait_n=(!STRESS||ticks%113<70)&&!(CASE<2&&!mr&&a==24'h07ffff&&cpu.u0.write&&forced<6);
 // The vector device holds DI for the whole IORQ pulse, including after M1 rises.
 wire [7:0] din=!io?8'hfe:!mr&&!rd?mem[a]:8'hff;
 G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(clk),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(1'b1),.DI(din),.A24(a),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
 reg [23:0] expected_return,after_pc,ei_pc,frame_sp,frame_ret;integer k;
 function automatic [23:0] word_at(input [23:0] adr);word_at={mem[adr+2],mem[adr+1],mem[adr]};endfunction
 always @(posedge clk)if(reset_n)begin
  if(!mr&&!wr)mem[a]<=dout;
  if(!rf&&a[23:16]!=0)$fatal(1,"refresh retained bank");
  if(ce)begin
   if(CASE<2&&!mr&&a==24'h07ffff&&cpu.u0.write)begin
    if(forced<6)forced<=forced+1;
    if(!triggered&&!wr)begin irq<=1;triggered<=1;if(CASE==1)begin nmi<=1;pulse<=8;end end
   end
   if(CASE==2&&!halt_n&&!triggered)begin nmi<=1;pulse<=8;triggered<=1;end
   if((CASE==3||CASE==4||CASE==5)&&!triggered&&a==ei_pc&&cpu.u0.mcycle==1&&cpu.u0.tstate==2)begin irq<=1;triggered<=1;if(CASE==4)begin nmi<=1;pulse<=8;end end
   if(pulse>0)begin pulse<=pulse-1;if(pulse==1)nmi<=0;end
   if(CASE==2&&!second_nmi&&triggered&&!nmi&&cpu.u0.nmicycle&&cpu.u0.mcycle==3&&cpu.u0.tstate==2)begin nmi<=1;pulse<=8;second_nmi<=1;end
   if(!io&&!m1)begin
    if((CASE==1||CASE==4)&&mem[24'h030401]!==8'ha1)$fatal(1,"IRQ won over pending NMI");irq<=0;
   end
   if((cpu.u0.intcycle||cpu.u0.nmicycle)&&cpu.u0.mcycle==1&&cpu.u0.tstate==1&&!old_entry)begin
    entries=entries+1;if(cpu.u0.nmicycle)nmis=nmis+1;else acks=acks+1;
    frame_sp=CASE==3?24'h000001:(CASE==2&&entries==2)?24'h04fffe:24'h050001;
    frame_ret=CASE==2?(entries==1?after_pc:24'h000066):expected_return;
   end
   old_entry<=(cpu.u0.intcycle||cpu.u0.nmicycle)&&cpu.u0.mcycle==1&&cpu.u0.tstate==1;
   now_state={a,dout,cpu.u0.pc,cpu.u0.spl,mr};
   if(cpu.u0.tstate==2&&!cpu.u0.wait_n)begin
    if(hold_valid&&now_state!==held)$fatal(1,"PC/SPL/bus changed during WAIT");held=now_state;hold_valid=1;waits=waits+1;
   end else hold_valid=0;
   if(cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n&&a==24'h000200)begin
    if(cpu.u0.adl_mode!==0||cpu.u0.sp!==16'hf000||cpu.u0.spl!==(CASE==3?24'h1:24'h050001))$fatal(1,"return mode/SP corrupted SPS=%h SPL=%h",cpu.u0.sp,cpu.u0.spl);
    if(entries!=(CASE==5?1:(CASE==1||CASE==2||CASE==4?2:1))||writes!=(CASE==5?0:entries*3))$fatal(1,"entry/write coverage entries=%d writes=%d",entries,writes);
    if(CASE<2)begin
     if(word_at(24'h030420)!==24'h2||word_at(24'h030423)!==24'h040000||word_at(24'h030426)!==24'h080000)$fatal(1,"interrupt not at first complete block byte BC=%h HL=%h DE=%h",word_at(24'h030420),word_at(24'h030423),word_at(24'h030426));
     if({mem[24'h080001],mem[24'h080000],mem[24'h07ffff]}!==24'hd78231)$fatal(1,"block copy/restart failed");
     if(mem[24'h030400]!==8'h5a)$fatal(1,"IRQ handler not executed");
    end
    if(CASE==2&&(nmis!=2||mem[24'h030401]!==2))$fatal(1,"nested/pending NMI lost nmis=%d count=%h",nmis,mem[24'h030401]);
    if(CASE==3&&word_at(24'h030430)!==24'hfffffe)$fatal(1,"IM2 wrap frame not SPL24");
    if(STRESS&&waits==0)$fatal(1,"no WAIT coverage");
    $display("PASS irq_unit_r11 case=%d stress=%d phase=%d entries=%d writes=%d waits=%d",CASE,STRESS,PHASE,entries,writes,waits);$finish;
   end
  end
  if(!mr&&!wr&&!old_write&&cpu.u0.irq_long)begin
   k=writes%3;
   if(a!==((frame_sp-1-k)&24'hffffff)||dout!==((frame_ret>>(8*(2-k)))&8'hff))$fatal(1,"entry frame mismatch a=%h expect=%h data=%h ret=%h k=%d",a,((frame_sp-1-k)&24'hffffff),dout,frame_ret,k);
   writes=writes+1;
  end
  old_write<=!mr&&!wr;
 end
 initial begin
  case(CASE)
  0:begin
  `include "irq_unit_r11/case0.vh"
  end
  1:begin
  `include "irq_unit_r11/case1.vh"
  end
  2:begin
  `include "irq_unit_r11/case2.vh"
  end
  3:begin
  `include "irq_unit_r11/case3.vh"
  end
  4:begin
  `include "irq_unit_r11/case4.vh"
  end
  5:begin
  `include "irq_unit_r11/case5.vh"
  end
  endcase
  repeat(12)@(negedge clk);reset_n=1;
 end
 initial begin #100000000;$fatal(1,"unit timeout pc=%h SPL=%h MC=%h entries=%d nmis=%d",cpu.u0.pc,cpu.u0.spl,cpu.u0.mcycle,entries,nmis);end
`include "request_checks_r11_1.vh"
endmodule
