`timescale 1ns/1ps
module tb_rst_r18;
 parameter CASE=0,CPU_DIV=4,STRESS=0,PHASE=0,FAULT=0,MAXTIME=180000000;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer tick=0,div=0;reg run=1;
 always @(posedge clk)begin
  tick<=tick+1;
  if(!reset_n)begin div<=PHASE%CPU_DIV;run<=1;end
  else if(div==CPU_DIV-1)begin div<=0;run<=!STRESS||tick%257<180;end else div<=div+1;
 end
 wire ce=div==0&&run,cf=div==CPU_DIV/2&&run,wait_n=!STRESS||tick%113<70;
 reg[7:0] mem[0:16777215];wire[23:0] a;wire[15:0] msx;wire ew,mr,io,rd,wr,rf,m1,halt_n,busak;wire[7:0] dout;
 reg irq=0,nmi=0,busrq=1;integer pulse=0;
 wire[7:0] din=!io?8'hfe:!mr&&!rd?mem[a]:8'hff;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(reset_n),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(busrq),.BUSAK_n(busak),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ew),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(halt_n),.DO(dout));
 reg[23:0] epc[0:2047],ewa[0:31],halt_pc,trigger_pc,initial_spl;
 reg[7:0] e_acc[0:2047],e_flags[0:2047],e_marker[0:2047],ewd[0:31];reg[15:0]e_sp[0:2047],initial_sp;reg[23:0]e_spl[0:2047];
 reg eadl[0:2047],emad[0:2047],e_ief[0:2047],check_acc[0:2047],check_flags[0:2047],check_marker[0:2047],check_sp[0:2047],check_spl[0:2047],check_ief[0:2047],seen[0:2047];
 reg[23:0] va[0:3];reg[7:0] vd[0:3];integer nvector=0;reg vector_ready=0;
 integer i,nchecks=0,checked=0,nwrites=0,writes=0,entries=0,expected_entries=0,guard=0,guard_kind=0,waits=0,pauses=0;
 reg pending_nmi=0,pending_irq=0,triggered=0,nested=0,irq_pending=0,old_write=0,old_start=0,old_halt=1;
 reg held_valid=0;reg[175:0]held,now_state;reg old_ce;
 reg[126:0] frozen;integer frame_waits=0,frame_pauses=0,guard_ticks=0;
 reg bus_triggered=0,bus_granted=0;integer bus_hold=0;
 always @(posedge clk)if(reset_n)begin
  if(!mr&&!wr)mem[a]<=dout;
  if(ce)begin
   // Install the private vector after boot, so vector 00 cannot replace the reset entry.
   if(cpu.u0.frame_start&&!guard&&!vector_ready)begin
    for(i=0;i<nvector;i=i+1)mem[va[i]]=vd[i];vector_ready=1;
   end
   if(!wait_n)waits=waits+1;
   if(!triggered&&((halt_pc!=0&&!halt_n)||(trigger_pc!=0&&a==trigger_pc&&cpu.mcycle==1&&cpu.tstate==2&&cpu.u0.wait_n)))begin
    triggered=1;
    if(halt_pc!=0)begin nmi<=1;pulse<=8;end else irq<=1;
   end
   if(pulse>0)begin pulse<=pulse-1;if(pulse==1)nmi<=0;end
   if(pending_nmi&&!nested&&cpu.u0.frame_state==1&&cpu.u0.frame_ts==2)begin nested=1;nmi<=1;pulse<=8;end
   if(pending_irq&&!irq_pending&&cpu.u0.frame_returning)begin irq_pending=1;irq<=1;end
   if(!io&&!m1)irq<=0;
   if(cpu.u0.frame_start&&!old_start&&!cpu.u0.frame_return)entries=entries+1;
   old_start<=cpu.u0.frame_start;
   // Request a bus grant during a frame, and keep it pending through the frame.
   if(STRESS&&!guard&&!bus_triggered&&cpu.u0.frame_active&&cpu.u0.frame_ts==2)begin bus_triggered=1;busrq<=0;end
   if(bus_triggered&&!busak)begin bus_granted=1;bus_hold=bus_hold+1;if(bus_hold>=3)busrq<=1;end
   now_state={a,dout,cpu.u0.pc,cpu.u0.spl,cpu.u0.sp,cpu.u0.acc,cpu.u0.f,cpu.u0.frame_state,cpu.u0.frame_count};
   if(cpu.u0.frame_active&&cpu.u0.frame_ts==2&&!cpu.u0.wait_n)begin
    if(held_valid&&now_state!==held)$fatal(1,"frame changed during WAIT");held=now_state;held_valid=1;frame_waits=frame_waits+1;
   end else held_valid=0;
   if(cpu.mcycle==1&&cpu.tstate==2&&cpu.u0.wait_n&&busak&&halt_n&&!mr&&!rd&&io&&!cpu.u0.intcycle&&!cpu.u0.nmicycle)begin
    for(i=0;i<nchecks;i=i+1)if(entries>0&&a==epc[i]&&!seen[i])begin
     if(cpu.u0.adl_mode!==eadl[i]||cpu.u0.madl!==emad[i]||(check_acc[i]&&cpu.u0.acc!==e_acc[i])||(check_flags[i]&&cpu.u0.f!==e_flags[i])||
      (check_sp[i]&&cpu.u0.sp!==e_sp[i])||(check_spl[i]&&cpu.u0.spl!==e_spl[i])||(check_ief[i]&&cpu.u0.inte_ff1!==e_ief[i])||(check_marker[i]&&mem[24'h030400]!==e_marker[i]))
      $fatal(1,"MADL state ADDR=%h ADL=%b/%b MADL=%b/%b A=%h/%h F=%h/%h SP=%h/%h SPL=%h/%h IEF=%b/%b marker=%h/%h",a,cpu.u0.adl_mode,eadl[i],cpu.u0.madl,emad[i],cpu.u0.acc,e_acc[i],cpu.u0.f,e_flags[i],cpu.u0.sp,e_sp[i],cpu.u0.spl,e_spl[i],cpu.u0.inte_ff1,e_ief[i],mem[24'h030400],e_marker[i]);
     
     checked=checked+1;seen[i]=1;
    end
    if(a==24'h000200)begin
     if(checked!=nchecks||writes!=nwrites||entries!=expected_entries||cpu.u0.adl_mode!==0||cpu.u0.madl!==0||cpu.u0.mbase!==0)$fatal(1,"MADL coverage checked=%d/%d writes=%d/%d entries=%d/%d",checked,nchecks,writes,nwrites,entries,expected_entries);
     if(STRESS&&waits==0)$fatal(1,"no WAIT coverage");
     if((pending_nmi||pending_irq)&&mem[24'h030420]!==8'h5a)$fatal(1,"interrupt handler marker missing");
     if(pending_nmi&&!nested)$fatal(1,"no nested NMI");if(pending_irq&&!irq_pending)$fatal(1,"no pending IRQ");
     $display("PASS rst_r18 case=%0d div=%0d stress=%0d checks=%0d frame_writes=%0d entries=%0d WAIT=%0d frame_WAIT=%0d pause=%0d bus_grant=%b",CASE,CPU_DIV,STRESS,checked,writes,entries,waits,frame_waits,frame_pauses,bus_granted);$finish;
    end
   end
   if(guard&&!halt_n)begin
    guard_ticks=guard_ticks+1;
    if(cpu.u0.sp!==initial_sp||cpu.u0.spl!==initial_spl||writes!=0)$fatal(1,"guard changed stack");
    if(guard_ticks==5)begin $display("PASS rst_r18 guard=%0d",guard_kind);$finish;end
   end
  end
  if(cpu.u0.frame_active&&!wr&&!old_write)begin
   if(writes>=nwrites||a!==ewa[writes]||dout!==ewd[writes])$fatal(1,"frame write ADDR=%h EXP_ADDR=%h EXP=%h ACT=%h n=%0d",a,ewa[writes],ewd[writes],dout,writes);
   writes=writes+1;
  end
  old_write<=!wr;
 end
 always @(posedge clk)begin
  old_ce=ce;frozen={cpu.u0.pc,cpu.u0.spl,cpu.u0.sp,cpu.u0.acc,cpu.u0.f,cpu.u0.frame_state,cpu.u0.frame_ts,cpu.u0.frame_count};
  #0.002;
  if(reset_n&&cpu.u0.frame_active&&!old_ce)begin
   if(frozen!=={cpu.u0.pc,cpu.u0.spl,cpu.u0.sp,cpu.u0.acc,cpu.u0.f,cpu.u0.frame_state,cpu.u0.frame_ts,cpu.u0.frame_count})$fatal(1,"frame advanced without CEN");
   frame_pauses=frame_pauses+1;
  end
  if(reset_n&&cpu.u0.frame_active&&!busak)$fatal(1,"bus granted inside frame");
 end
 always @(posedge clk or negedge clk)begin #0.004;
  if(reset_n&&busak&&(^a)!==1'bx)begin
   if(!rf&&a[23:16]!=0)$fatal(1,"refresh bank");
   if(!io&&a[23:16]!=0)$fatal(1,"I/O bank");
   if(rf&&(ew!==(a[23:16]!=0)||msx!==(a[23:16]!=0?16'h0000:a[15:0])))$fatal(1,"MSX isolation");
  end
 end
 initial begin
  for(i=0;i<2048;i=i+1)seen[i]=0;
  `include "rst_r18/select.vh"
  if(FAULT==2)force cpu.u0.frame_sps=1'b0;
  repeat(12)@(negedge clk);reset_n=1;
 end
 initial begin #MAXTIME;$fatal(1,"MADL timeout PC=%h A=%h Fstate=%d FTS=%d SP=%h SPL=%h INT=%b NMI=%b checked=%d/%d",cpu.u0.pc,a,cpu.u0.frame_state,cpu.u0.frame_ts,cpu.u0.sp,cpu.u0.spl,irq,nmi,checked,nchecks);end
generate if(FAULT==1)begin
 always @(cpu.u0.frame_state) if(cpu.u0.frame_state==1)force cpu.u0.data_out_reg=8'h00;else release cpu.u0.data_out_reg;
end endgenerate
integer debug_n=0;
always @(posedge clk)if(debug_n<250&&$test$plusargs("DEBUG")&&reset_n&&ce&&(cpu.u0.frame_active||cpu.u0.frame_start||(cpu.u0.pc>=24'h8200&&cpu.u0.pc<24'h8210)||cpu.u0.pc==24'h38||cpu.u0.pc>=24'h0b0000&&cpu.u0.pc<24'h0b0030))
 begin debug_n=debug_n+1;$display("DBG A=%h PC=%h IR=%h MC=%d TS=%d fstate=%d fts=%d cnt=%d CEN=%b IRQ=%b/%b IEF=%b trig=%b fstart=%b DI=%h SP=%h SPL=%h marker=%h NMIcy=%b Is=%b Pref=%b WP=%b Halt=%b clken=%b",a,cpu.u0.pc,cpu.u0.ir,cpu.u0.mcycle,cpu.u0.tstate,cpu.u0.frame_state,cpu.u0.frame_ts,cpu.u0.frame_count,ce,irq,cpu.u0.int_s,cpu.u0.inte_ff1,triggered,cpu.u0.frame_start,cpu.u0.di_reg,cpu.u0.sp,cpu.u0.spl,mem[24'h30400],cpu.u0.nmicycle,cpu.u0.iset,cpu.u0.prefix,cpu.u0.width_pending,cpu.u0.halt_ff,cpu.u0.clken);end
endmodule
