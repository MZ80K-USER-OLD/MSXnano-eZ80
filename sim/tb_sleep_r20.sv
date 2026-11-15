`timescale 1ns/1ps
module tb_sleep_r20;
 parameter CTX=2,STRESS=0,CPU_DIV=4,FAULT=0,PREBUS=0;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer tick=0,div=0;reg run=1;
 always @(posedge clk)begin tick<=tick+1;if(!reset_n)begin div<=0;run<=1;end
 else if(div==CPU_DIV-1)begin div<=0;run<=!STRESS||tick%197<140;end else div<=div+1;end
 wire ce=div==0&&run,cf=div==CPU_DIV/2&&run;
 reg waiting=0,irq=0,nmi=0,busrq=0;wire wn=!waiting&&(!STRESS||tick%103<80);
 wire[23:0]a;wire[15:0]msx;wire ext,mr,io,rd,wr,rf,m1,hn,ba;wire[7:0]dout;
 reg[7:0]mem[0:16777215];wire[7:0]din=!io?8'hff:!mr&&!rd?mem[a]:8'hff;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(reset_n),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wn),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(!busrq),.BUSAK_n(ba),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ext),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(hn),.DO(dout));
 integer wi,ev,passed=0,k,c=0;reg[23:0]p,start_pc,after_pc,op_pc;reg[7:0]pref;reg started=0;reg[191:0]snapshot;reg[23:0]held_a;reg[7:0]held_d;
 wire[191:0] state={cpu.u0.pc,cpu.u0.sp,cpu.u0.spl,cpu.u0.f,cpu.u0.acc,cpu.u0.r,cpu.u0.i,cpu.u0.istatus,cpu.u0.adl_mode,cpu.u0.madl,cpu.u0.mbase,cpu.u0.inte_ff1,cpu.u0.inte_ff2,cpu.u0.mcycle,cpu.u0.tstate};
 task emit(input[7:0]v);begin mem[p]=v;p=p+1;end endtask
 task w24(input[23:0]v);begin emit(v[7:0]);emit(v[15:8]);emit(v[23:16]);end endtask
 task build;
 begin
  p=0;emit(8'hc3);emit(0);emit(1);p=24'h100;emit(8'hf3);emit(8'h31);emit(1);emit(8'hc0);
  emit(8'hed);emit(8'h5e); // IM2 must not silently become IM1.
  if(CTX!=0)begin
   emit(1);emit(8'he7);emit(8'he7);emit(8'h3e);emit(8'ha5);emit(8'hed);emit(8'h79);emit(8'h3e);emit(8'h5a);emit(8'hed);emit(8'h79);
   emit(8'h5b);emit(8'hc3);w24(24'h0a1000);p=24'h0a1000;
   emit(8'h31);w24(24'h050001);emit(8'h3e);emit(14);emit(8'hed);emit(8'h6d);
   emit(8'hed);emit((CTX==3||CTX==4)?8'h7d:8'h7e);
  end
  // Carry/S/Z/P/H seed; SLP must preserve AF and IEF. EI ensures pending
  // interrupts at SLP completion cannot accidentally start a frame.
  if(CTX!=0)begin emit(1);w24(24'ha6d7);emit(8'hc5);emit(8'hf1);end
  emit(8'hfb);emit(0);
  start_pc=CTX==0?24'h20fc:((CTX==1||CTX==4)?24'h0efffe:24'h0afffe);
  if(CTX==0)begin emit(8'hc3);emit(start_pc[7:0]);emit(start_pc[15:8]);end
  else begin emit((CTX==1||CTX==4)?8'h40:8'h5b);emit(8'hc3);emit(start_pc[7:0]);emit(start_pc[15:8]);if(CTX==2||CTX==3)emit(start_pc[23:16]);end
  p=start_pc;case(wi)1:pref=8'h40;2:pref=8'h49;3:pref=8'h52;4:pref=8'h5b;default:pref=0;endcase
  if(wi)emit(pref);emit(8'hed);op_pc=p;emit(8'h76);after_pc=p;
  if(CTX==1||CTX==4)begin after_pc={8'h0e,p[15:0]};op_pc={8'h0e,op_pc[15:0]};end
  // For Z80 crossing FFFF, move bytes that were provisionally emitted above.
  if(CTX==1||CTX==4)for(k=0;k<5;k=k+1)mem[{8'h0e,16'(start_pc+k)}]=mem[start_pc+k];
  mem[after_pc]=8'h76;mem[24'h66]=8'h76;mem[24'h38]=8'h76;
 end endtask
 always @(posedge clk)if(reset_n)begin
  if(!mr&&!wr)mem[a]<=dout;
  if(CTX!=0&&!started&&ce&&cpu.u0.mcycle==1&&cpu.u0.tstate==2&&cpu.u0.wait_n&&a==op_pc)begin
   started=1;if(PREBUS)busrq<=1;if(ev==1||ev==3)irq<=1;if(ev==2||ev==3)nmi<=1;
  end
  if(PREBUS&&started&&ba&&ce&&cpu.u0.mcycle==1&&cpu.u0.tstate==2&&a==after_pc&&!cpu.sleep_i)$fatal(1,"SLP skipped after BUSRQ");
 end
 initial begin
  for(wi=0;wi<(CTX==0?1:5);wi=wi+1)for(ev=0;ev<(CTX==0?1:4);ev=ev+1)begin
   reset_n=0;waiting=0;irq=0;nmi=0;busrq=0;started=0;repeat(4)@(negedge clk);build();repeat(12)@(negedge clk);reset_n=1;
   if(CTX==0)begin
    wait(!mr&&!rd&&a==after_pc);@(negedge clk);
    if(cpu.sleep_i!==0||cpu.u0.istatus!==1)$fatal(1,"SLP locked ED76 alias lost");
   end else begin
    if(PREBUS)begin wait(ba===0);repeat(80)@(negedge clk);busrq=0;end
    wait(cpu.sleep_i===1);@(negedge clk);
    if(cpu.u0.pc!==(CTX==1||CTX==4?{8'h00,after_pc[15:0]}:after_pc)+(FAULT?1:0))$fatal(1,"SLP PC EXP=%h ACT=%h",after_pc,cpu.u0.pc);
    if(cpu.u0.istatus!==2||cpu.u0.f!==8'hd7||cpu.u0.acc!==8'ha6||cpu.u0.width_pending!==0||cpu.u0.inte_ff1!==1||cpu.u0.inte_ff2!==1)$fatal(1,"SLP entry side effects");
    snapshot=state;held_a=a;held_d=dout;
    for(c=0;c<120;)begin
     @(negedge clk);if(ce)begin
      c=c+1;
      if(c>15)begin irq=1;nmi=c<50;busrq=c>60;waiting=c>30;end
     end
     #1;
     if(cpu.sleep_i!==1||state!==snapshot||a!==held_a||dout!==held_d||{mr,io,rd,wr,rf,m1,hn,ba}!==8'b11111101)$fatal(1,"SLP hold/bus failure ctx=%0d width=%0d ev=%0d c=%0d bus=%b",CTX,wi,ev,c,{mr,io,rd,wr,rf,m1,hn,ba});
    end
    // RESET is the production wake mechanism. Remove all requests and boot a
    // small locked Z80 program; no diagnostic escape exists in this DUT.
    reset_n=0;irq=0;nmi=0;busrq=0;waiting=0;p=0;emit(8'hc3);emit(0);emit(2);mem[24'h200]=8'h76;
    repeat(12)@(negedge clk);reset_n=1;wait(!mr&&!rd&&a==24'h200);@(negedge clk);
    if(cpu.sleep_i!==0||cpu.u0.adl_mode!==0||cpu.u0.extensions_enabled!==0||cpu.u0.inte_ff1!==0)$fatal(1,"SLP reset state");
   end
   passed=passed+1;
  end
  $display("PASS SLP cases=%0d ctx=%0d stress=%0d",passed,CTX,STRESS);$finish;
 end
 initial begin #100000000;$fatal(1,"SLP timeout ctx=%0d width=%0d event=%0d pc=%h sleep=%b",CTX,wi,ev,cpu.u0.pc,cpu.sleep_i);end
endmodule
