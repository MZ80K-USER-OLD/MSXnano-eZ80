`timescale 1ns/1ps
// External peripheral oracle, independent of the CPU's frame counter/decoder.
module tb_im0_r19;
 parameter CTX=0,STRESS=0,CPU_DIV=4,FAULT=0,HALT_SRC=0,NMI_RACE=0,NMI_DURING=0;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer ticks=0,div=0;reg run=1;
 always @(posedge clk) begin
  ticks<=ticks+1;
  if(!reset_n)begin div<=STRESS?7%CPU_DIV:0;run<=1;end
  else if(div==CPU_DIV-1)begin div<=0;run<=!STRESS||ticks%257<180;end else div<=div+1;
 end
 wire ce=div==0&&run,cf=div==CPU_DIV/2&&run;
 wire wn=!STRESS||ticks%113<70;
 reg[7:0] mem[0:16777215];reg irq=0,busrq=1,nmi=0,nmi_sent=0;integer nmi_pulse=0,nmi_seen=0;
 wire[23:0] a;wire[15:0] msx;wire ext,mr,io,rd,wr,rf,m1,halt_n,busak;wire[7:0] dout;
 integer opcode,first=0,last=255,selected=-1;
 wire[7:0] din=!io?opcode[7:0]:!mr&&!rd?mem[a]:8'hff;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(reset_n),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wn),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(busrq),.BUSAK_n(busak),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ext),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(halt_n),.DO(dout));
 reg[23:0] p,start_pc,ack_pc,resume_pc,stack0,entry_sp,handler_pc;
 integer source_adl,madl,valid,iscall,vec,nframe,nwrites,nreads,nacks,passed=0,k;
 reg done_case=0,triggered=0,old_ack=0,old_wr=0,old_rd=0,handler_seen=0,resume_seen=0;
 reg grant_requested=0,grant_seen=0;integer grant_ticks=0;
 reg[23:0] expected_a[0:3];reg[7:0] expected_d[0:3];
 reg hold_valid=0;reg[82:0] held,now_state;
 task emit(input[7:0] x);begin mem[p]=x;if(p[23:16]==8'h0e)p={8'h0e,p[15:0]+16'd1};else p=p+1;end endtask
 task word24(input[23:0] x);begin emit(x[7:0]);emit(x[15:8]);emit(x[23:16]);end endtask
 task build;
  begin
   source_adl=CTX!=2;madl=CTX!=0;
   iscall=opcode==8'hcd;
   valid=iscall||opcode==8'hc7||opcode==8'hcf||opcode==8'hd7||opcode==8'hdf||opcode==8'he7||opcode==8'hef||opcode==8'hf7||opcode==8'hff;
   vec=opcode&8'h38;
   stack0=STRESS?(iscall?24'h000001:24'h040001):24'h050001;
   start_pc=source_adl?24'h0afffd:24'h0efffd;
   ack_pc=start_pc+2;
   resume_pc=iscall?(source_adl?ack_pc+3:24'h0e0002):ack_pc;
   nframe=valid?(source_adl?3:2)+madl:0;
   entry_sp=(stack0-nframe)&24'hffffff;
   p=0;emit(8'hc3);emit(0);emit(1);
   p=24'h100;emit(8'hf3);emit(8'h31);emit(1);emit(8'hc0);
   emit(1);emit(8'he7);emit(8'he7);emit(8'h3e);emit(8'ha5);emit(8'hed);emit(8'h79);emit(8'h3e);emit(8'h5a);emit(8'hed);emit(8'h79);
   emit(8'h5b);emit(8'hc3);word24(24'h0a1000);
   p=24'h0a1000;emit(8'h31);word24(stack0);emit(8'h3e);emit(14);emit(8'hed);emit(8'h6d);
   if(madl)begin emit(8'hed);emit(8'h7d);end
   emit(8'hed);emit(8'h46);
   emit(8'h11);word24(24'h123456);emit(8'h21);word24(24'h654321);emit(8'hdd);emit(8'h21);word24(24'h456789);emit(8'hfd);emit(8'h21);word24(24'h765432);
   emit(1);word24(24'ha6d7);emit(8'hc5);emit(8'hf1);
   emit(source_adl?8'h5b:8'h40);emit(8'hc3);emit(start_pc[7:0]);emit(start_pc[15:8]);if(source_adl)emit(start_pc[23:16]);
   p=start_pc;emit(8'hfb);emit(HALT_SRC?8'h76:0);
   if(iscall)begin
    mem[ack_pc]=0;mem[source_adl?ack_pc+1:24'h0e0000]=8'h90;mem[source_adl?ack_pc+2:24'h0e0001]=8'h0c;
   end
   p=resume_pc;emit(8'hf3);
   emit(8'h5b);emit(8'hed);emit(8'h43);word24(24'h0d1000);
   emit(8'h5b);emit(8'hed);emit(8'h53);word24(24'h0d1003);
   emit(8'h5b);emit(8'h22);word24(24'h0d1006);
   emit(8'h5b);emit(8'hdd);emit(8'h22);word24(24'h0d1009);
   emit(8'h5b);emit(8'hfd);emit(8'h22);word24(24'h0d100c);
   emit(8'h5b);emit(8'hc3);word24(24'h0a7000);
   p=24'h0a7000;emit(8'hed);emit(8'h7e);emit(8'h3e);emit(0);emit(8'hed);emit(8'h6d);emit(8'h40);emit(8'hc3);emit(0);emit(2);
   p=24'h0c9000;emit(8'h3e);emit(8'h5a);emit(8'hed);if(madl)begin mem[p-1]=8'h5b;emit(8'hed);end emit(8'h4d);
   handler_pc=iscall?24'h0c9000:vec;
   p=24'h66;emit(madl?8'h5b:0);emit(8'hed);emit(8'h45);
   for(k=0;k<nframe;k=k+1)begin
    expected_a[k]=(stack0-1-k)&24'hffffff;
    expected_d[k]=(k<(source_adl?3:2))?resume_pc>>(8*((source_adl?3:2)-1-k)):2+source_adl;
   end
   if(FAULT&&nframe)expected_d[0]=expected_d[0]^1;
   done_case=0;triggered=0;old_ack=0;old_wr=0;old_rd=0;handler_seen=0;resume_seen=0;
   nwrites=0;nreads=0;nacks=0;irq=0;busrq=1;nmi=0;nmi_sent=0;nmi_pulse=0;nmi_seen=0;grant_requested=0;grant_seen=0;grant_ticks=0;hold_valid=0;
  end
 endtask
 always @(posedge clk)if(reset_n)begin
  if(!mr&&!wr)mem[a]<=dout;
  if(!io&&cpu.u0.intcycle&&!old_ack)begin
   nacks=nacks+1;irq<=0;
   if(nacks!=1)$fatal(1,"extra IM0 IACK op=%h",opcode);
   // Install the private bank-zero vector only after the reset entry is gone.
   if(valid&&!iscall)begin mem[vec]=8'hc3;mem[vec+1]=0;mem[vec+2]=8'h90;mem[vec+3]=8'h0c;end
  end
  old_ack<=!io&&cpu.u0.intcycle;
  if(cpu.u0.frame_active&&cpu.u0.intcycle&&!mr&&!wr&&!old_wr)begin
   if(nwrites>=nframe||a!==expected_a[nwrites]||dout!==expected_d[nwrites])
    $fatal(1,"IM0 frame write op=%h k=%d a=%h d=%h expected=%h/%h",opcode,nwrites,a,dout,expected_a[nwrites],expected_d[nwrites]);
   nwrites=nwrites+1;
  end
  old_wr<=!mr&&!wr;
  if(cpu.u0.frame_active&&cpu.u0.frame_state==2&&cpu.u0.frame_is_call&&!mr&&!rd&&!old_rd)begin
   if(!iscall||nreads>=3||a!==(source_adl?ack_pc+nreads:24'h0e0000|((ack_pc+nreads)&16'hffff)))$fatal(1,"IM0 CALL operand address %h",a);
   nreads=nreads+1;
  end
  old_rd<=!mr&&!rd;
  if(ce)begin
   if(!nmi_sent&&((NMI_RACE&&a==start_pc+1&&cpu.u0.mcycle==1&&cpu.u0.tstate==2)||(NMI_DURING&&valid&&cpu.u0.frame_active&&cpu.u0.frame_ts==2)))begin nmi_sent=1;nmi<=1;nmi_pulse=8;end
   else if(nmi_pulse>0)begin nmi_pulse=nmi_pulse-1;if(nmi_pulse==0)nmi<=0;end
   if(cpu.u0.nmicycle)nmi_seen=1;
   if(!triggered&&a==start_pc&&cpu.u0.mcycle==1&&cpu.u0.tstate==2)begin triggered=1;irq<=1;end
   if(STRESS&&!grant_requested&&cpu.u0.frame_active)begin grant_requested=1;busrq<=0;end
   if(grant_requested&&!busak)begin grant_seen=1;grant_ticks=grant_ticks+1;if(grant_ticks>=3)busrq<=1;end
   now_state={a,dout,cpu.u0.pc,cpu.u0.spl,cpu.u0.frame_ts};
   if(cpu.u0.frame_active&&cpu.u0.frame_ts==2&&!cpu.u0.wait_n)begin
    if(hold_valid&&now_state!==held)$fatal(1,"IM0 frame changed under WAIT");held=now_state;hold_valid=1;
   end else hold_valid=0;
   if(cpu.mcycle==1&&cpu.tstate==2&&!mr&&!rd&&cpu.u0.wait_n)begin
    if(valid&&nacks&&a==handler_pc&&!handler_seen)begin
     handler_seen=1;
     if(cpu.u0.spl!==entry_sp||cpu.u0.sp!==16'hc001||cpu.u0.adl_mode!==1||cpu.u0.acc!==8'ha6||cpu.u0.f!==8'hd7||cpu.u0.inte_ff1!==0||cpu.u0.inte_ff2!==0)$fatal(1,"IM0 entry state op=%h SPL=%h A/F=%h/%h",opcode,cpu.u0.spl,cpu.u0.acc,cpu.u0.f);
     if(nwrites!=nframe||nreads!=(iscall?3:0))$fatal(1,"IM0 entry transfer counts");
    end
    if(a==resume_pc&&nacks&&!resume_seen)begin
     resume_seen=1;
     if(cpu.u0.spl!==stack0||cpu.u0.sp!==16'hc001||cpu.u0.adl_mode!==source_adl||cpu.u0.inte_ff1!==0||cpu.u0.inte_ff2!==0)$fatal(1,"IM0 return state op=%h",opcode);
     if(!valid&&(cpu.u0.acc!==8'ha6||cpu.u0.f!==8'hd7||nwrites!=0))$fatal(1,"unsupported IM0 byte had effects op=%h",opcode);
    end
    if(a==24'h200)begin
     if({mem[24'h0d1002],mem[24'h0d1001],mem[24'h0d1000]}!==24'h00a6d7||
        {mem[24'h0d1005],mem[24'h0d1004],mem[24'h0d1003]}!==24'h123456||
        {mem[24'h0d1008],mem[24'h0d1007],mem[24'h0d1006]}!==24'h654321||
        {mem[24'h0d100b],mem[24'h0d100a],mem[24'h0d1009]}!==24'h456789||
        {mem[24'h0d100e],mem[24'h0d100d],mem[24'h0d100c]}!==24'h765432)$fatal(1,"IM0 changed BC/DE/HL/IX/IY opcode=%h",opcode);
     if(!triggered||nacks!=1||!resume_seen||handler_seen!==valid||nwrites!=nframe)$fatal(1,"IM0 coverage op=%h ack=%d handler=%d resume=%d writes=%d",opcode,nacks,handler_seen,resume_seen,nwrites);
     if((NMI_RACE||(NMI_DURING&&valid))&&!nmi_seen)$fatal(1,"NMI coverage missing");
     if(STRESS&&grant_requested&&!grant_seen)$fatal(1,"pending BUSRQ never granted");
     done_case=1;
    end
   end
  end
 end
 initial begin
  if($value$plusargs("OP=%d",selected))begin first=selected;last=selected;end
  for(opcode=first;opcode<=last;opcode=opcode+1)begin
   reset_n=0;repeat(3)@(negedge clk);build();repeat(10)@(negedge clk);reset_n=1;
   wait(done_case);passed=passed+1;$display("PASS im0_r19 ctx=%0d stress=%0d opcode=%02h",CTX,STRESS,opcode);
  end
  $display("PASS IM0 matrix cases=%0d",passed);$finish;
 end
 initial begin #400000000;$fatal(1,"IM0 timeout op=%h pc=%h frame=%h ts=%h mc=%h irq=%h",opcode,cpu.u0.pc,cpu.u0.frame_state,cpu.u0.frame_ts,cpu.u0.mcycle,cpu.u0.intcycle);end
endmodule
