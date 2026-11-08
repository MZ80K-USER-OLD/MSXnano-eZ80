`timescale 1ns/1ps
module tb_exsp_work_r11_2;
 parameter PAIR=0,NMI=0,TRIGGER_MC=2;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer ticks=0;reg [3:0] div=0;reg enabled=1;
 always @(posedge clk)begin ticks<=ticks+1;if(!reset_n)div<=PAIR*3+NMI+TRIGGER_MC;else begin div<=div+1;if(div==15)enabled<=ticks%257<180;end end
 wire ce=div==0&&enabled,cf=div==8&&enabled;
 wire [23:0] a;wire mr,io,rf,rd,wr,m1,halt_n;wire [7:0] dout;
 reg [7:0] mem[0:16777215];reg irq=0,nmi=0,triggered=0;integer pulse=0,forced=0,entries=0,writes=0,reads=0,holds=0;reg old_write=0;
 wire target=cpu.u0.ex_sp_long&&cpu.u0.mcycle==TRIGGER_MC&&cpu.u0.tstate==2;
 wire wait_n=(ticks%113<70)&&!(target&&forced<6);
 wire [7:0] din=!io?8'hfe:!mr&&!rd?mem[a]:8'hff;
 G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(clk),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(1'b1),.DI(din),.A24(a),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
 reg [23:0] after_pc;reg old_entry=0,checked_return=0;reg holding=0;reg [47:0] held_work;
 always @(posedge clk)if(reset_n)begin
  if(!mr&&!wr)mem[a]<=dout;
  if(!mr&&!wr&&!old_write&&cpu.u0.ex_sp_long)begin
   if(writes>=3||a!==(24'h04fffe+writes)||dout!==((24'h123456>>(writes*8))&8'hff))$fatal(1,"EXSP write address/data order");writes=writes+1;
  end
  old_write<=!mr&&!wr;
  if(ce)begin
   if(target)begin forced<=forced+1;if(!triggered)begin triggered<=1;if(NMI)begin nmi<=1;pulse<=8;end else irq<=1;end end
   if(pulse>0)begin pulse<=pulse-1;if(pulse==1)nmi<=0;end
   if(!io&&!m1)irq<=0;
   if(cpu.u0.ex_sp_long&&cpu.u0.tstate==2&&!cpu.u0.wait_n)begin
    if(holding&&held_work!=={cpu.u0.ex_sp_source,cpu.u0.ex_sp_address})$fatal(1,"EXSP work changed during WAIT");
    held_work={cpu.u0.ex_sp_source,cpu.u0.ex_sp_address};holding=1;holds=holds+1;
   end else holding=0;
   if(cpu.u0.ex_sp_long&&cpu.u0.tstate==2&&cpu.u0.wait_n&&cpu.u0.mcycle>=2&&cpu.u0.mcycle<=4)reads=reads+1;
   if((cpu.u0.intcycle||cpu.u0.nmicycle)&&cpu.u0.mcycle==1&&cpu.u0.tstate==1&&!old_entry)begin
    if(reads!=3||writes!=3)$fatal(1,"interrupt accepted before EXSP completed");entries=entries+1;
   end
   old_entry<=(cpu.u0.intcycle||cpu.u0.nmicycle)&&cpu.u0.mcycle==1&&cpu.u0.tstate==1;
   if(cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n&&a==after_pc)begin
    if(cpu.u0.f!==8'hd7||cpu.u0.spl!==24'h04fffe||entries!=1)$fatal(1,"EXSP/ISR flags or SPL restore");checked_return=1;
   end
   if(cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n&&a==24'h000200)begin
    if(!checked_return||entries!=1||reads!=3||writes!=3||holds==0||mem[24'h030410]!==8'ha7||{mem[24'h030402],mem[24'h030401],mem[24'h030400]}!==24'hc37ea1||{mem[24'h050000],mem[24'h04ffff],mem[24'h04fffe]}!==24'h123456)$fatal(1,"EXSP final result/coverage");
    $display("PASS EXSP work pair=%d NMI=%d trigger_MC=%d reads=%d writes=%d WAIT=%d",PAIR,NMI,TRIGGER_MC,reads,writes,holds);$finish;
   end
  end
 end
 initial begin
  case(PAIR)
  0:begin
   `include "exsp_work_r11_2/pair0.vh"
  end
  1:begin
   `include "exsp_work_r11_2/pair1.vh"
  end
  2:begin
   `include "exsp_work_r11_2/pair2.vh"
  end
  endcase
  repeat(12)@(negedge clk);reset_n=1;
 end
 initial begin #20000000;$fatal(1,"EXSP timeout");end
endmodule
