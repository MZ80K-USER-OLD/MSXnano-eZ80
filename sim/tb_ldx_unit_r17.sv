`timescale 1ns/1ps
`ifndef TEST_HEADER
`define TEST_HEADER "test.vh"
`endif
`include `TEST_HEADER
module tb_ldx_unit_r17;
parameter CPU_DIV=4, PHASE=0, PAUSE=0, FAULT=0, IRQ_STRESS=0;
reg clk=0, reset_n=0;always #10 clk=~clk;
integer tick=0;always @(posedge clk)tick<=tick+1;
reg run=1;always @(posedge clk)if(tick%CPU_DIV==(PHASE+CPU_DIV-1)%CPU_DIV)run<=!PAUSE || tick%71<50;
wire en=tick%CPU_DIV==PHASE%CPU_DIV && run;
wire falling=tick%CPU_DIV==(PHASE+CPU_DIV/2)%CPU_DIV && run;
wire wait_n=tick%23>=9;
wire [23:0] a;wire [15:0] msx;wire ext,mr,io,rf,rd,wr,m1,halt_n;
wire [7:0] dout;reg[7:0] mem[0:1048575];
wire[7:0] di=!mr&&!rd?mem[a[19:0]]:8'hff;
G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(clk),.clk_enable(en),.clk_falling(falling),.WAIT_n(wait_n),.INT_n(IRQ_STRESS==2),.NMI_n(nmi_pin),.BUSRQ_n(1'b1),.DI(di),.A24(a),.A_MSX(msx),.Extended_Window(ext),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
integer i,indirect_seen=0,waits=0,pauses=0,interrupts=0;reg old_irq=0;reg nmi_pin=1;
always @(posedge clk)if(reset_n && IRQ_STRESS==2)begin
 if(cpu.u0.pair_indirect && cpu.u0.mcycle==2)nmi_pin<=0;
 else if(!cpu.u0.pair_indirect)nmi_pin<=1;
end
reg[2:0] hold_mc;reg old_active=0,old_hold=0;reg[23:0] hold_addr;reg[7:0] hold_data;
always @(posedge clk)if(reset_n)begin
 if(!mr&&!wr)mem[a[19:0]]<=(FAULT && a==24'h03ffff)?dout^8'h01:dout;
 if(ext && msx!==0)$fatal(1,"MSX bus not isolated %h",a);
 if(ext && a[23:16]==0)$fatal(1,"wrong extended qualification %h",a);
 if((cpu.u0.intcycle||cpu.u0.nmicycle) && !old_irq)interrupts=interrupts+1;old_irq<=cpu.u0.intcycle||cpu.u0.nmicycle;
 if((!IRQ_STRESS && cpu.u0.intcycle) || (IRQ_STRESS!=2 && cpu.u0.nmicycle))$fatal(1,"IRQ accepted during DI transfer");
 if(cpu.u0.pair_indirect && !old_active)indirect_seen=indirect_seen+1;
 old_active<=cpu.u0.pair_indirect;
 if(cpu.u0.pair_indirect && !wait_n)waits=waits+1;
 if(cpu.u0.pair_indirect && !run)pauses=pauses+1;
 if(!halt_n)begin
  if(mem[`X17_STATUS]!== (FAULT?2:1))$fatal(1,"unit failed status=%h act=%h exp=%h pc=%h",mem[`X17_STATUS],mem[`X17_DIAG_ACT],mem[`X17_DIAG_EXP],cpu.u0.pc);
  if(!FAULT && indirect_seen!=80)$fatal(1,"instruction coverage %d",indirect_seen);
  if(IRQ_STRESS && interrupts!=80)$fatal(1,"IRQ boundary coverage %d",interrupts);
  if(waits==0 || (PAUSE && pauses==0))$fatal(1,"missing stress coverage");
  $display("PASS ldx_unit_r17 instructions=%0d WAIT=%0d pause=%0d fault=%0d",indirect_seen,waits,pauses,FAULT);$finish;
 end
end
// Compare consecutive enabled stalled T2 edges after registered outputs settle.
always @(posedge clk)if(reset_n && en)begin
 if(cpu.u0.pair_indirect && cpu.u0.mcycle>=2 && cpu.u0.tstate==2 && !wait_n && !mr)begin
  #0.001;
  if(old_hold && hold_mc==cpu.u0.mcycle && (a!==hold_addr || (!wr && dout!==hold_data)))
   $fatal(1,"request changed across accepted stalled T2 edges");
  old_hold=1;hold_addr=a;hold_data=dout;hold_mc=cpu.u0.mcycle;
 end else old_hold=0;
end
initial begin
 for(i=0;i<1048576;i=i+1)mem[i]=0;
 mem[0]=8'hc3;mem[1]=0;mem[2]=1;
 if(IRQ_STRESS)$readmemh("sim/ldx_r17/test_irq.hex",mem,16'h100,`X17_END);
 else $readmemh("sim/ldx_r17/test.hex",mem,16'h100,`X17_END);
 // Ordinary Z80 IM1 handler: preserve AF, mark entry, RETI.
 mem['h38]='hf5;mem['h39]='h3e;mem['h3a]='h5a;mem['h3b]='h32;mem['h3c]=0;mem['h3d]='he0;mem['h3e]='hf1;mem['h3f]='hed;mem['h40]='h4d;
 for(i=0;i<9;i=i+1)mem['h66+i]=mem['h38+i];mem['h6e]='h45;
 #113;reset_n=1;
 #100000000;$fatal(1,"unit timeout pc=%h",cpu.u0.pc);
end
endmodule
