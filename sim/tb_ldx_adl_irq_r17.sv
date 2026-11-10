`timescale 1ns/1ps
module tb_ldx_adl_irq_r17;
parameter NMI=0,CPU_DIV=4,PHASE=0,STRESS=0;
reg clk=0,reset_n=0;always #10 clk=~clk;
integer ticks=0,div=0;reg run=1;
always @(posedge clk)begin
 ticks<=ticks+1;
 if(!reset_n)begin div<=PHASE%CPU_DIV;run<=1;end
 else if(div==CPU_DIV-1)begin div<=0;run<=!STRESS || ticks%257<180;end else div<=div+1;
end
wire ce=div==0&&run,cf=div==CPU_DIV/2&&run;
wire wait_n=!STRESS || ticks%113<70;
reg [7:0] mem[0:16777215];wire[23:0] a;wire[15:0] msx;wire ew,mr,io,rd,wr,rf,m1,halt_n;wire[7:0] dout;
reg irq=0,nmi=0,old_entry=0;integer entries=0,completed=0,waits=0,frame_writes=0,frame_reads=0;
wire[7:0] din=!io?8'hff:!mr&&!rd?mem[a]:8'hff;
G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(reset_n),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(1'b1),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ew),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(halt_n),.DO(dout));
reg[23:0] epc[0:511];reg[7:0] eacc[0:511],ef[0:511];reg check_a[0:511],check_f[0:511],seen[0:511];integer nchecks=0,checked=0,i;
always @(posedge clk)if(reset_n)begin
 if(!mr&&!wr)mem[a]<=dout;
 if(ce)begin
  if(cpu.u0.mcycle>=2 && cpu.u0.mcycle<=4 && cpu.u0.tstate==2 && cpu.u0.wait_n && (cpu.u0.irq_long||cpu.u0.irq_return))begin
   if(a<24'h05007d || a>24'h05007f || mr || (cpu.u0.irq_long && wr) || (cpu.u0.irq_return && rd))
    $fatal(1,"native frame did not use SPL24 addr=%h IRQ=%b RET=%b",a,cpu.u0.irq_long,cpu.u0.irq_return);
   if(cpu.u0.irq_long)frame_writes=frame_writes+1;else frame_reads=frame_reads+1;
  end
  if(cpu.u0.pair_indexed && !wait_n)waits=waits+1;
  if(cpu.u0.pair_indexed && cpu.u0.mcycle==2)begin if(NMI)nmi<=1;else irq<=1;end
  if(cpu.u0.pair_indexed && cpu.u0.t_res && cpu.u0.mcycle==cpu.u0.mcycles)completed=completed+1;
  if((cpu.u0.intcycle||cpu.u0.nmicycle)&&!old_entry)begin
   entries=entries+1;if(entries>completed)$fatal(1,"interrupt accepted before indexed transfer end");
  end
  old_entry<=cpu.u0.intcycle||cpu.u0.nmicycle;
  if(!cpu.u0.pair_indexed)nmi<=0;
  if(!io&&!m1)irq<=0;
  if(!mr&&!m1&&cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n&&!cpu.u0.intcycle&&!cpu.u0.nmicycle)begin
   for(i=0;i<nchecks;i=i+1)if(a==epc[i]&&!seen[i])begin
    if(cpu.u0.adl_mode!==1||cpu.u0.mbase!==14||(check_a[i]&&cpu.u0.acc!==eacc[i])||(check_f[i]&&cpu.u0.f!==ef[i]))$fatal(1,"native ADL state pc=%h A=%h/%h F=%h/%h ADL=%b",a,cpu.u0.acc,eacc[i],cpu.u0.f,ef[i],cpu.u0.adl_mode);
    seen[i]=1;checked=checked+1;
   end
   if(a==24'h0a8000)begin
    for(i=0;i<nchecks;i=i+1)if(!seen[i])$display("MISSING pc=%h A=%h F=%h",epc[i],eacc[i],ef[i]);
    if(checked!=nchecks||frame_writes!=120||frame_reads!=120||entries!=40||completed!=40||cpu.u0.spl!==24'h050080||cpu.u0.sp!==16'hf000||(STRESS&&waits==0))$fatal(1,"coverage/stack checked=%d/%d irq=%d completed=%d SPL=%h SPS=%h",checked,nchecks,entries,completed,cpu.u0.spl,cpu.u0.sp);
    $display("PASS ldx_adl_irq_r17 NMI=%d div=%d stress=%d checks=%d entries=%d waits=%d frame_W=%d frame_R=%d",NMI,CPU_DIV,STRESS,checked,entries,waits,frame_writes,frame_reads);$finish;
   end
  end
 end
end
always @(posedge clk or negedge clk)begin #0.002;
 if(reset_n&&rf&&(^a)!==1'bx)if(ew!==(a[23:16]!=0)||msx!==(a[23:16]!=0?16'h0000:a[15:0]))$fatal(1,"MSX isolation %h",a);
end
initial begin
 for(i=0;i<512;i=i+1)seen[i]=0;
 `include "ldx_adl_irq_r17/test.vh"
 repeat(12)@(negedge clk);reset_n=1;
 #150000000;$fatal(1,"native IRQ timeout pc=%h entries=%d",cpu.u0.pc,entries);
end
endmodule
