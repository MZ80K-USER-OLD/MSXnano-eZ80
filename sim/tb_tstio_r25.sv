`timescale 1ns/1ps
module tb_tstio_r25;
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
wire busrq_n=!STRESS||tick%809<750;
reg [7:0]mem[0:16777215];wire[23:0]a;wire[15:0]msx;wire ew,mr,io,rd,wr,rf,m1,halt_n;wire[7:0]dout;
wire[7:0]din=!io? a[15:8]^a[7:0]^8'ha5 : !mr&&!rd?mem[a]:8'hff;
reg irq_request=0,nmi_request=0,issued=0,old_interrupt=0;integer irq_events=0,reads_before_request=0,nmi_ticks=0;
G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(reset_n),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(!irq_request),.NMI_n(!nmi_request),.BUSRQ_n(busrq_n),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ew),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(halt_n),.DO(dout));
reg [191:0] gp_before;reg [15:0] sps_before;reg [23:0] spl_before;integer gi;
reg[23:0]epc[0:1023],ebc[0:1023];reg[7:0]ea[0:1023],ef[0:1023];integer ereads[0:1023];integer nchecks,expected_reads,checked=0,reads=0,i,waits=0;reg old_read=0;
always @(posedge clk)if(reset_n)begin
 if(!mr&&!wr)mem[a]<=dout;
 if(!io&&!rd&&!old_read)begin
  reads=reads+1;
  if(a[23:8]!==0||!mr)$fatal(1,"TSTIO I/O qualification ADDR=%h MREQ=%b",a,mr);
 end
 old_read<=!io&&!rd;
 if((cpu.u0.intcycle||cpu.u0.nmicycle)&&!old_interrupt)begin
  if(CASE>=3 && reads<=reads_before_request)$fatal(1,"interrupt accepted before TSTIO I/O read");
  irq_events=irq_events+1;irq_request<=0;
 end
 old_interrupt<=cpu.u0.intcycle||cpu.u0.nmicycle;
 if(ce)begin
  if(cpu.u0.exec_control[53] && cpu.u0.mcycle==1 && cpu.u0.tstate==4 && !cpu.u0.intcycle && !cpu.u0.nmicycle)begin
   for(gi=0;gi<8;gi=gi+1)gp_before[gi*24+:24]={cpu.u0.regs.upper_view[63-gi*8-:8],cpu.u0.regs.regsh[gi],cpu.u0.regs.regsl[gi]};
   sps_before=cpu.u0.sp;spl_before=cpu.u0.spl;
  end
  if(CASE>=3 && cpu.u0.exec_control[53] && !cpu.u0.intcycle && !cpu.u0.nmicycle)begin
   if(cpu.u0.mcycle==1 && cpu.u0.tstate==4)issued=0;
   if(cpu.u0.mcycle==2 && cpu.u0.tstate==2 && !issued)begin
    issued=1;reads_before_request=reads;
    if(CASE<=4)irq_request<=1;else begin nmi_request<=1;nmi_ticks=8;end
   end
  end
  if(nmi_ticks>0)begin nmi_ticks=nmi_ticks-1;if(nmi_ticks==0)nmi_request<=0;end
  if(!wait_n)waits=waits+1;
  if(cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n&&!cpu.u0.intcycle&&!cpu.u0.nmicycle)begin
   i=checked;
   if(checked<nchecks&&a==epc[i])begin
    if(cpu.u0.acc!==ea[i]||cpu.u0.f!==ef[i]) $fatal(1,"TSTIO state ADDR=%h A=%h/%h F=%h/%h mask=%h",a,cpu.u0.acc,ea[i],cpu.u0.f,ef[i],cpu.u0.tmpaddr[7:0]);
    // Select BC through a separately generated ordinary LD BC probe is unnecessary:
    // inspect all stored bytes by their fixed architectural index in the baseline regfile.
    if({cpu.u0.regs.upper_view[63:56],cpu.u0.regs.regsh[0],cpu.u0.regs.regsl[0]}!==ebc[i])$fatal(1,"TSTIO BC changed");
    if(CASE!=2)begin
     for(gi=0;gi<8;gi=gi+1)if({cpu.u0.regs.upper_view[63-gi*8-:8],cpu.u0.regs.regsh[gi],cpu.u0.regs.regsl[gi]}!==gp_before[gi*24+:24])$fatal(1,"TSTIO GP changed index=%0d",gi);
     if(cpu.u0.sp!==sps_before || cpu.u0.spl!==spl_before)$fatal(1,"TSTIO SPS/SPL changed");
    end
    if(reads!=ereads[i])$fatal(1,"TSTIO read count %0d/%0d",reads,ereads[i]);
    checked=checked+1;
   end
   if(a==24'h000200)begin
    if(checked!=nchecks||reads!=expected_reads||cpu.u0.adl_mode!==0)$fatal(1,"TSTIO coverage %d/%d reads=%d/%d",checked,nchecks,reads,expected_reads);
    if(CASE>=3&&irq_events!=expected_reads)$fatal(1,"IRQ/NMI coverage %0d/%0d",irq_events,expected_reads);
    if(STRESS&&waits==0)$fatal(1,"no WAIT coverage");
    $display("PASS tstio_r25 case=%0d stress=%0d checks=%0d reads=%0d waits=%0d",CASE,STRESS,checked,reads,waits);$finish;
   end
  end
 end
end
initial begin
 case(CASE)
 0:begin
 `include "tstio_r25/case0.vh"
 end
 1:begin
 `include "tstio_r25/case1.vh"
 end
 2:begin
 `include "tstio_r25/case2.vh"
 end
 3:begin
 `include "tstio_r25/case3.vh"
 end
 4:begin
 `include "tstio_r25/case4.vh"
 end
 5:begin
 `include "tstio_r25/case5.vh"
 end
 6:begin
 `include "tstio_r25/case6.vh"
 end

 endcase
 repeat(12)@(negedge clk);reset_n=1;
end
initial begin #150000000;$fatal(1,"TSTIO timeout a=%h pc=%h checks=%0d/%0d",a,cpu.u0.pc,checked,nchecks);end
endmodule
