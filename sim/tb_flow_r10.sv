`timescale 1ns/1ps
module tb_flow_r10;
 parameter STRESS=0, PHASE=0, FAULT=0;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer ticks=0;reg [3:0] divider=0;reg enable_run=1;
 always @(posedge clk)begin
  ticks<=ticks+1;
  if(!reset_n)begin divider<=PHASE;enable_run<=1;end
  else begin divider<=divider+1;if(divider==15)enable_run<=!STRESS || ticks%257<180;end
 end
 wire ce=divider==0&&enable_run,cf=divider==8&&enable_run;
 wire wait_n=!STRESS || ticks%113<70;
 wire [23:0] a;wire mr,io,rf,rd,wr,m1,halt_n;wire [7:0] dout;
 reg [7:0] mem[0:16777215];
 wire [7:0] din=(!mr&&!rd)?(mem[a]^((FAULT==1&&cpu.u0.ctrl_ret&&cpu.u0.mcycle==4)?8'h01:8'h00)):8'hff;
 G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(clk),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(1'b0),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),.A24(a),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
 reg [23:0] epc[0:2047],esp[0:2047],ewa[0:1023],era[0:1023];
 reg eadl[0:2047];
 reg [7:0] eop[0:2047],ef[0:2047],ewd[0:1023],erd[0:1023];
 integer nfetch,nwrites,nreads,fetches=0,writes=0,reads=0,waits=0,pauses=0;
 reg active=0,oldwrite=0,vectors=0;reg [80:0] held,now_state;reg hold_valid=0;
 always @(posedge clk)if(reset_n)begin
  if(!mr&&!wr)mem[a]<=dout^((FAULT==2&&cpu.u0.ctrl_call&&cpu.u0.mcycle==7)?8'h01:8'h00);
  if(!io&&!m1)$fatal(1,"IRQ dispatched during DI/ADL");
  if(!rf&&a[23:16]!=0)$fatal(1,"refresh not bank zero");
  if(!enable_run)pauses=pauses+1;
  if(!halt_n)$fatal(1,"unexpected HALT pc=%h a=%h",cpu.u0.pc,a);
  if(!mr&&!wr&&!oldwrite&&active)begin
   if(writes>=nwrites || a!==ewa[writes] || dout!==ewd[writes])$fatal(1,"stack write %d a=%h expected=%h data=%h expected=%h pc=%h",writes,a,ewa[writes],dout,ewd[writes],cpu.u0.pc);
   writes=writes+1;
  end
  oldwrite<=!mr&&!wr;
  if(ce)begin
   now_state={a,dout,cpu.u0.pc,cpu.u0.spl,mr};
   if(cpu.u0.tstate==2&&!cpu.u0.wait_n)begin
    if(hold_valid&&now_state!==held)$fatal(1,"bus/PC/SPL changed during WAIT");held=now_state;hold_valid=1;waits=waits+1;
   end else hold_valid=0;
   if(cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n)begin
    if(a==24'h01e000)begin
     active=1;
     if(!vectors)begin for(integer v=0;v<8;v=v+1)mem[v*8]=8'hc9;vectors=1;end
    end
    if(active)begin
     if(a==24'h000200)begin
      if(fetches!=nfetch||writes!=nwrites||reads!=nreads||cpu.u0.adl_mode!==0||cpu.u0.sp!==16'hf000||cpu.u0.spl!==24'h000001)$fatal(1,"coverage/return mismatch fetch=%d/%d writes=%d/%d reads=%d/%d SPL=%h",fetches,nfetch,writes,nwrites,reads,nreads,cpu.u0.spl);
      if(STRESS&&(waits==0||pauses==0))$fatal(1,"no stress coverage");
      $display("PASS flow_r10 stress=%0d phase=%0d fetch=%0d writes=%0d reads=%0d WAIT=%0d pauses=%0d",STRESS,PHASE,fetches,writes,reads,waits,pauses);$finish;
     end
     // Initial F before the first seed operation is outside the test contract.
     if(fetches>=nfetch||a!==epc[fetches]||din!==eop[fetches]||cpu.u0.adl_mode!==eadl[fetches]||cpu.u0.spl!==esp[fetches]||(fetches>3&&cpu.u0.f!==ef[fetches]))$fatal(1,"fetch %d a=%h exp=%h op=%h exp=%h SPL=%h exp=%h F=%h exp=%h MC=%h",fetches,a,epc[fetches],din,eop[fetches],cpu.u0.spl,esp[fetches],cpu.u0.f,ef[fetches],cpu.u0.mcycle);
     fetches=fetches+1;
    end
   end
   if(active&&cpu.u0.mcycle!=1&&cpu.u0.tstate==2&&cpu.u0.wait_n&&!rd&&!mr&&(cpu.u0.ctrl_ret||cpu.u0.wide_stack&&cpu.u0.ir==8'hf1))begin
    if(reads>=nreads||a!==era[reads]||din!==erd[reads])$fatal(1,"stack read %d a=%h exp=%h data=%h exp=%h",reads,a,era[reads],din,erd[reads]);reads=reads+1;
   end
  end
 end
 initial begin
  `include "flow_r10/plan.vh"
  repeat(12)@(negedge clk);reset_n=1;
 end
 initial begin #300000000;$fatal(1,"flow timeout pc=%h a=%h fetches=%d",cpu.u0.pc,a,fetches);end
endmodule
