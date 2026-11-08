`timescale 1ns/1ps
module tb_tst_r15;
 parameter CASE=0,CPU_DIV=4,STRESS=0,PHASE=0,FAULT=0;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer tick=0,div=0;reg run=1;
 always @(posedge clk)begin
  tick<=tick+1;
  if(!reset_n)begin div<=PHASE%CPU_DIV;run<=1;end
  else if(div==CPU_DIV-1)begin div<=0;run<=!STRESS||tick%257<180;end else div<=div+1;
 end
 wire ce=div==0&&run,cf=div==CPU_DIV/2&&run;
 wire wait_n=!STRESS||tick%113<70;
 reg [7:0] mem[0:16777215];wire [23:0] a;wire [15:0] msx;wire ew,mr,io,rd,wr,rf,m1,halt_n;wire [7:0] dout;
 reg irq=0,nmi=0;integer pulse=0,haltn=0,entries=0;reg old_halt=1,old_write=0;
 wire[7:0] din=!io?8'hfe:!mr&&!rd?mem[a]:8'hff;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(reset_n),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(1'b1),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ew),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(halt_n),.DO(dout));
 reg[23:0] epc[0:8191],halt_pc[0:5];reg[7:0] eacc[0:8191],ef[0:8191],emb[0:8191];reg eadl[0:8191],check_a[0:8191],check_f[0:8191],seen[0:8191];integer nchecks=0,checked=0,i,waits=0,banked_fetches=0,writes=0;reg fetched=0;
 always @(posedge clk)if(reset_n)begin
  if(FAULT==2&&cpu.u0.adl_mode)force cpu.u0.acc=8'h00;
  if(!mr&&!wr)mem[a]<=dout;
  if(!mr&&!wr&&!old_write)writes=writes+1;old_write<=!mr&&!wr;
  if(!rf&&a[23:16]!=0)$fatal(1,"refresh bank leaked ADDR=%h",a);
  if(!io&&a[23:16]!=0)$fatal(1,"I/O bank leaked ADDR=%h",a);
  if(ce)begin
   if(!wait_n)waits=waits+1;
   if(!halt_n&&old_halt&&CASE==99)begin
    if(haltn>=6)$fatal(1,"extra HALT");
    if((haltn==2||haltn==5))begin nmi<=1;pulse<=8;end else irq<=1;
    haltn=haltn+1;
   end
   old_halt<=halt_n;
   if(pulse>0)begin pulse<=pulse-1;if(pulse==1)nmi<=0;end
   if(!io&&!m1)irq<=0;
   if(cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n)begin
    if(a[23:16]!=0&&!cpu.u0.adl_mode)begin
     if(a[23:16]!==cpu.u0.mbase)$fatal(1,"banked Z80 fetch ADDR=%h EXP=%h ACT=%h",a,cpu.u0.mbase,a[23:16]);
     banked_fetches=banked_fetches+1;
    end
    i=checked;
    if(checked<nchecks&&a==epc[i])begin
     if(cpu.u0.mbase!==emb[i]||cpu.u0.adl_mode!==eadl[i]||(check_a[i]&&cpu.u0.acc!==eacc[i])||(check_f[i]&&cpu.u0.f!==ef[i]))
      $fatal(1,"MBASE state ADDR=%h MB_EXP=%h MB_ACT=%h A_EXP=%h A_ACT=%h F_EXP=%h F_ACT=%h ADL=%b/%b",a,emb[i],cpu.u0.mbase,eacc[i],cpu.u0.acc,ef[i],cpu.u0.f,eadl[i],cpu.u0.adl_mode);
     seen[i]=1;checked=checked+1;
    end
    if(a==(CASE>=3?24'h007f00:24'h000200))begin
     if(checked!=nchecks||cpu.u0.mbase!==0||cpu.u0.adl_mode!==0)$fatal(1,"coverage/cleanup checked=%d/%d MB=%h ADL=%b",checked,nchecks,cpu.u0.mbase,cpu.u0.adl_mode);
     if(STRESS&&waits==0)$fatal(1,"no WAIT");
     if(CASE==99)begin
      if({mem[24'h0e0000],mem[24'h0effff]}!==16'h1234||{mem[24'h0e9011],mem[24'h0e9010]}!==16'h0001||cpu.u0.istatus!==2||banked_fetches==0)$fatal(1,"wrap/SPS/IM mismatch FFFF=%h 0000=%h SPS=%h/%h IM=%h",mem[24'h0effff],mem[24'h0e0000],mem[24'h0e9011],mem[24'h0e9010],cpu.u0.istatus);
     end
     if(CASE==99&&(haltn!=6||cpu.u0.sp!==16'h0001||cpu.u0.spl!==24'h050080||banked_fetches==0))$fatal(1,"IRQ return frame mismatch SPS=%h SPL=%h halts=%d",cpu.u0.sp,cpu.u0.spl,haltn);
     $display("PASS tst_r15 case=%0d div=%0d stress=%0d checks=%0d waits=%0d banked_fetches=%0d",CASE,CPU_DIV,STRESS,checked,waits,banked_fetches);$finish;
    end
   end
  end
 end
 always @(posedge clk or negedge clk)begin #0.002;
  if(reset_n&&rf&&(^a)!==1'bx)begin
   if(ew!==(a[23:16]!=0)||msx!==(a[23:16]!=0?16'h0000:a[15:0]))$fatal(1,"MSX isolation ADDR=%h MSX=%h EW=%b",a,msx,ew);
  end
 end
 initial begin
  for(i=0;i<8192;i=i+1)seen[i]=0;
  case(CASE)
 0:begin
 `include "tst_r15/case0.vh"
 end
 1:begin
 `include "tst_r15/case1.vh"
 end
 2:begin
 `include "tst_r15/case2.vh"
 end
 3:begin
 `include "tst_r15/case3.vh"
 end
 4:begin
 `include "tst_r15/case4.vh"
 end
 endcase
  if(FAULT==1)force cpu.u0.f=8'h00;
  
  repeat(12)@(negedge clk);reset_n=1;
 end
 initial begin #500000000;$fatal(1,"timeout PC=%h ADDR=%h ADL=%b MB=%h MC=%h TS=%h checked=%d/%d halt=%d",cpu.u0.pc,a,cpu.u0.adl_mode,cpu.u0.mbase,cpu.u0.mcycle,cpu.u0.tstate,checked,nchecks,haltn);end
endmodule
