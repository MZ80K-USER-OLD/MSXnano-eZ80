`timescale 1ns/1ps
module tb_prefix_r19_1;
 parameter EVENT=0,INJECT=0,STRESS=0,CPU_DIV=4,FAULT=0;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer tick=0,div=0;reg run=1;
 always @(posedge clk)begin
  tick<=tick+1;
  if(!reset_n)begin div<=STRESS?7%CPU_DIV:0;run<=1;end
  else if(div==CPU_DIV-1)begin div<=0;run<=!STRESS||tick%257<180;end else div<=div+1;
 end
 wire ce=div==0&&run,cf=div==CPU_DIV/2&&run,wn=!STRESS||tick%113<70;
 reg[7:0] mem[0:16777215];reg irq=0,nmi=0;integer pulse=0;
 wire[23:0] a;wire[15:0] msx;wire ext,mr,io,rd,wr,rf,m1,halt_n;wire[7:0] dout;
 wire[7:0] din=!io?8'hff:!mr&&!rd?mem[a]:8'hff;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(reset_n),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wn),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(1'b1),.BUSAK_n(),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ext),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(halt_n),.DO(dout));
 integer ci,first=0,last=495,selected=-1,opindex,source_adl,iy,wi,x,y,k,passed=0;
 integer reads=0,writes=0,entries=0,frame_writes=0;
 reg[7:0] pref,op,disp,initial_data,result_data;reg[23:0] p,start_pc,after_pc,target,alias_addr,handler,retpc;
 reg done_case=0,triggered=0,old_rd=0,old_wr=0,old_entry=0,after_seen=0;
 function automatic [23:0] stream_next(input [23:0] adr,input integer n);
  stream_next=source_adl?(adr+n):{8'h0e,16'((adr+n)&16'hffff)};
 endfunction
 task emit(input[7:0] v);begin mem[p]=v;if(p[23:16]==8'h0e)p={8'h0e,p[15:0]+16'd1};else p=p+1;end endtask
 task word24(input[23:0] v);begin emit(v[7:0]);emit(v[15:8]);emit(v[23:16]);end endtask
 task check_operation;
  begin
   if(mem[target]!==result_data||reads!=1||writes!=(x==1?0:1))
    $fatal(1,"PREFIX data case=%0d ADDR=%h EXP=%h ACT=%h reads=%0d writes=%0d",ci,target,result_data,mem[target],reads,writes);
  end
 endtask
 task build;
  begin
   opindex=ci/16;source_adl=(ci/8)%2;iy=(ci/4)%2;wi=ci%4;
   case(wi)0:pref=8'h40;1:pref=8'h49;2:pref=8'h52;3:pref=8'h5b;endcase
   if(opindex<7)op=((opindex==6?7:opindex)<<3)|6;
   else op=8'h40+((opindex-7)/8)*64+((opindex-7)%8)*8+6;
   x=op>>6;y=(op>>3)&7;initial_data=8'h81;result_data=initial_data;
   if(x==0)case(y)
    0:result_data={initial_data[6:0],initial_data[7]};
    1:result_data={initial_data[0],initial_data[7:1]};
    2:result_data={initial_data[6:0],1'b1};
    3:result_data={1'b1,initial_data[7:1]};
    4:result_data=initial_data<<1;
    5:result_data={initial_data[7],initial_data[7:1]};
    7:result_data=initial_data>>1;
   endcase
   else if(x==2)result_data=initial_data&~(1<<y);
   else if(x==3)result_data=initial_data|(1<<y);
   disp=iy?8'h80:8'h7f;
   target=pref[3]?(iy?24'h03ff90:24'h03006f):(iy?24'h0eff90:24'h0e006f);
   alias_addr=pref[3]?(iy?24'h0eff90:24'h0e006f):(iy?24'h03ff90:24'h03006f);
   mem[target]=initial_data;mem[alias_addr]=8'h5a;
   if(FAULT)result_data=result_data^1;
   start_pc=source_adl?24'h0afffc:24'h0efffc;after_pc=stream_next(start_pc,5);
   handler=EVENT==1?24'h38:24'h66;
   p=0;emit(8'hc3);emit(0);emit(1);
   p=24'h100;emit(8'hf3);emit(8'h31);emit(1);emit(8'hc0);emit(1);emit(8'he7);emit(8'he7);
   emit(8'h3e);emit(8'ha5);emit(8'hed);emit(8'h79);emit(8'h3e);emit(8'h5a);emit(8'hed);emit(8'h79);emit(8'h5b);emit(8'hc3);word24(24'h0a1000);
   p=24'h0a1000;emit(8'h31);word24(24'h050001);emit(8'h3e);emit(14);emit(8'hed);emit(8'h6d);emit(8'hed);emit(8'h7d);emit(8'hed);emit(8'h56);
   emit(8'hdd);emit(8'h21);word24(24'h02fff0);emit(8'hfd);emit(8'h21);word24(24'h040010);
   emit(1);word24(24'ha6d7);emit(8'hc5);emit(8'hf1);
   // EI/NOP complete before injecting at a selected point in the prefix chain.
   if(EVENT)begin emit(8'hfb);emit(0);end
   emit(source_adl?8'h5b:8'h40);emit(8'hc3);emit(start_pc[7:0]);emit(start_pc[15:8]);if(source_adl)emit(start_pc[23:16]);
   p=start_pc;emit(pref);emit(iy?8'hfd:8'hdd);emit(8'hcb);emit(disp);emit(op);
   emit(8'h11);emit(8'h34);emit(8'hab);if(source_adl)emit(8'h12);
   emit(8'h5b);emit(8'hed);emit(8'h53);word24(24'h0d1000);
   emit(8'hf3);emit(8'h5b);emit(8'hc3);word24(24'h0a7000);
   p=24'h0a7000;emit(8'hed);emit(8'h7e);emit(8'h3e);emit(0);emit(8'hed);emit(8'h6d);emit(8'h40);emit(8'hc3);emit(0);emit(2);
   p=handler;emit(8'h5b);emit(8'hed);emit(EVENT==1?8'h4d:8'h45);
   irq=0;nmi=0;pulse=0;done_case=0;triggered=0;old_rd=0;old_wr=0;old_entry=0;after_seen=0;
   reads=0;writes=0;entries=0;frame_writes=0;
  end
 endtask
 always @(posedge clk)if(reset_n)begin
  if(!mr&&!wr)mem[a]<=dout;
  if(!mr&&!rd&&!old_rd&&a==target)reads=reads+1;
  if(!mr&&!wr&&!old_wr&&a==target)writes=writes+1;
  if(cpu.u0.frame_active&&!mr&&!wr&&!old_wr)begin
   k=frame_writes;
   if(k>source_adl+2||a!==(24'h050000-k)||dout!==(((k<(source_adl?3:2))?after_pc>>(8*((source_adl?3:2)-1-k)):2+source_adl)&32'hff))
    $fatal(1,"PREFIX interrupt frame case=%0d k=%0d a=%h d=%h return=%h",ci,k,a,dout,after_pc);
   frame_writes=frame_writes+1;
  end
  old_rd<=!mr&&!rd;old_wr<=!mr&&!wr;
  if(!io)irq<=0;
  if(ce)begin
   if(EVENT&&!triggered&&cpu.u0.tstate==2&&cpu.u0.wait_n&&
      ((INJECT<3&&cpu.u0.mcycle==1&&a==stream_next(start_pc,INJECT))||
       (INJECT==3&&cpu.u0.mcycle==6)||(INJECT==4&&cpu.u0.mcycle==7)))begin
    triggered=1;if(EVENT==1)irq<=1;else begin nmi<=1;pulse=8;end
   end
   if(pulse>0)begin pulse=pulse-1;if(pulse==0)nmi<=0;end
   if((cpu.u0.intcycle||cpu.u0.nmicycle)&&cpu.u0.mcycle==1&&cpu.u0.tstate==1&&!old_entry)begin
    entries=entries+1;
    if(cpu.u0.pc!=={(source_adl?after_pc[23:16]:8'h00),after_pc[15:0]})$fatal(1,"PREFIX interrupt split/late case=%0d PC=%h expected=%h",ci,cpu.u0.pc,after_pc);
    check_operation();
   end
   old_entry<=(cpu.u0.intcycle||cpu.u0.nmicycle)&&cpu.u0.mcycle==1&&cpu.u0.tstate==1;
   if(cpu.mcycle==1&&cpu.tstate==2&&cpu.u0.wait_n&&!mr&&!rd)begin
    if(a==after_pc&&!after_seen)begin
     check_operation();
     if(cpu.u0.width_pending!==0)$fatal(1,"PREFIX width leaked into next instruction case=%0d",ci);
     after_seen=1;
    end
    if(a==24'h200)begin
     if(!after_seen||entries!=(EVENT?1:0)||frame_writes!=(EVENT?(source_adl?4:3):0)||cpu.u0.spl!==24'h050001||cpu.u0.sp!==16'hc001)$fatal(1,"PREFIX final state/coverage case=%0d entries=%0d",ci,entries);
     if({mem[24'h0d1001],mem[24'h0d1000]}!==16'hab34||(source_adl&&mem[24'h0d1002]!==8'h12))$fatal(1,"PREFIX following instruction width corrupted case=%0d",ci);
     done_case=1;
    end
   end
  end
 end
 initial begin
  if($value$plusargs("CASE=%d",selected))begin first=selected;last=selected;end
  for(ci=first;ci<=last;ci=ci+1)if(EVENT==0||ci/16==7||ci/16==16||ci/16==25)begin
   reset_n=0;repeat(3)@(negedge clk);build();repeat(10)@(negedge clk);reset_n=1;
   wait(done_case);passed=passed+1;
  end
  $display("PASS PREFIX matrix cases=%0d event=%0d inject=%0d stress=%0d",passed,EVENT,INJECT,STRESS);$finish;
 end
 initial begin #800000000;$fatal(1,"PREFIX timeout case=%0d PC=%h MC=%h TS=%h pending=%b",ci,cpu.u0.pc,cpu.u0.mcycle,cpu.u0.tstate,cpu.u0.width_pending);end
endmodule
