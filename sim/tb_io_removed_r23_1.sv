`timescale 1ns/1ps
module tb_io_removed_r23_1;
 parameter STRESS=0, EVENT=0;
 reg clk=0,rst=0;always #10 clk=~clk;
 reg[3:0]div=0;integer ticks=0;reg run=1;
 always @(posedge clk)begin ticks<=ticks+1;if(!rst)begin div<=0;run<=1;end else if(div==(STRESS?14:3))begin div<=0;run<=!STRESS||ticks%257<180;end else div<=div+1;end
 wire ce=div==0&&run,cf=div==(STRESS?7:2)&&run,wn=!STRESS||ticks%113<70;
 reg[7:0]mem[0:1048575];wire[23:0]a;wire[15:0]msx;wire ext,mr,io,rf,rd,wr,m1,halt_n;wire[7:0]dout;
 reg irq=0,nmi=0;reg[7:0]input_data=0;
 wire[7:0]din=!io?(m1?input_data:8'hff):(!mr&&!rd?mem[a[19:0]]:8'hff);
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(rst),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wn),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(1'b1),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ext),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
 integer ci,k,passed=0,events=0,frames=0;reg[23:0]p,haltpc;reg[7:0]pref,mask,result,expected_flags;reg src,old_write=0,old_io=0,triggered=0,old_frame=0;reg[31:0]held;reg holding=0;
 task emit(input[7:0]v);begin mem[p[19:0]]=v;p=p+1;end endtask
 task w24(input[23:0]v);begin emit(v[7:0]);emit(v[15:8]);emit(v[23:16]);end endtask
 task pair(input[7:0]op,input[23:0]v);begin emit(op);w24(v);end endtask
 always @(posedge clk)if(rst)begin
  if(!mr&&!wr&&!old_write)mem[a[19:0]]<=dout;
  old_write<=!mr&&!wr;
  if(!io&&m1&&(!rd||!wr)&&a[15:0]!=16'he7e7)begin
   if(!old_io)begin events=events+1;
   end
   if(holding&&held!=={a,dout})$fatal(1,"TSTIO payload changed under WAIT");held={a,dout};holding=1;
   if(EVENT&&!triggered)begin if(EVENT==1)irq<=1;else nmi<=1;triggered=1;end
  end else holding=0;
  old_io<=!io&&m1&&(!rd||!wr)&&a[15:0]!=16'he7e7;
  if(!io&&!m1)irq<=0;
  if(ce&&(cpu.u0.intcycle||cpu.u0.nmicycle)&&!old_frame)begin
   frames=frames+1;nmi<=0;
  end
  if(ce)old_frame<=cpu.u0.intcycle||cpu.u0.nmicycle;
 end
 initial begin
 for(ci=0;ci<80;ci=ci+1)begin
  rst=0;irq=0;nmi=0;old_io=0;old_write=0;holding=0;triggered=0;old_frame=0;events=0;frames=0;
  src=(ci/8)%2;
  case(ci%6)0:input_data=0;1:input_data=1;2:input_data=8'h7f;3:input_data=8'h80;4:input_data=8'ha5;5:input_data=8'hff;endcase
  case((ci/6)%4)0:mask=0;1:mask=8'hff;2:mask=8'h81;3:mask=8'h5a;endcase
  case(ci/16)0:pref=0;1:pref=8'h40;2:pref=8'h49;3:pref=8'h52;4:pref=8'h5b;endcase
  result=input_data&mask;expected_flags=(result&8'ha8)|8'h10|(result==0?8'h40:0)|((^result)?0:8'h04);
  p=0;emit(8'hc3);emit(0);emit(1);
  p=24'h100;emit(8'hf3);emit(8'h31);emit(0);emit(8'hf0);
  emit(1);emit(8'he7);emit(8'he7);emit(8'h3e);emit(8'ha5);emit(8'hed);emit(8'h79);emit(8'h3e);emit(8'h5a);emit(8'hed);emit(8'h79);emit(8'h5b);emit(8'hc3);w24(24'h0a1000);p=24'h0a1000;
  pair(8'h31,24'h050100);pair(1,24'h00a62a);emit(8'h5b);emit(8'hc5);emit(8'h5b);emit(8'hf1);pair(1,24'h7af6e6);pair(8'h21,24'h123456);pair(8'h11,24'h789abc);emit(8'hdd);pair(8'h21,24'h2468ac);emit(8'hfd);pair(8'h21,24'h123456);
  emit(8'h3e);emit(14);emit(8'hed);emit(8'h6d);emit(8'h3e);emit(8'ha6);emit(8'hed);emit(8'h56);
  if(EVENT)begin emit(8'hfb);emit(0);end
  emit(src?8'h5b:8'h40);emit(8'hc3);emit(0);emit(8'h80);if(src)emit(8'h0a);p=src?24'h0a8000:24'h0e8000;
  if(pref)emit(pref);emit(8'hed);
  case(ci%8)0:emit(8'h84);1:emit(8'h8c);2:emit(8'ha4);3:emit(8'hac);4:emit(8'h94);5:emit(8'h9c);6:emit(8'hb4);7:emit(8'hbc);endcase
  emit(8'hf3);emit(8'h5b);emit(8'hc5);emit(8'h5b);emit(8'he5);emit(8'h5b);emit(8'hf5);emit(8'h5b);emit(8'hd5);emit(8'h5b);emit(8'hdd);emit(8'he5);emit(8'h5b);emit(8'hfd);emit(8'he5);haltpc=p;emit(8'h76);
  mem[24'h38]=8'hfb;mem[24'h39]=8'hed;mem[24'h3a]=8'h4d;mem[24'h66]=8'hed;mem[24'h67]=8'h45;
  mem[24'h0e0038]=8'hfb;mem[24'h0e0039]=8'hed;mem[24'h0e003a]=8'h4d;mem[24'h0e0066]=8'hed;mem[24'h0e0067]=8'h45;
  repeat(12)@(negedge clk);rst=1;k=0;
  while(halt_n!==0&&k<120000)begin @(negedge clk);k=k+1;end
  if(k>=120000)$fatal(1,"TSTIO timeout case=%d pc=%h",ci,cpu.u0.pc);
  if(events!=0)$fatal(1,"TSTIO IO count %d",events);
  if(mem[20'h500f7]!==8'h2a||mem[20'h500f8]!==8'ha6)$fatal(1,"TSTIO AF case=%d mask=%h data=%h F EXP=%h ACT=%h A=%h",ci,mask,input_data,expected_flags,mem[20'h500f7],mem[20'h500f8]);
  if({mem[20'h500ff],mem[20'h500fe],mem[20'h500fd]}!==24'h7af6e6||{mem[20'h500fc],mem[20'h500fb],mem[20'h500fa]}!==24'h123456||{mem[20'h500f6],mem[20'h500f5],mem[20'h500f4]}!==24'h789abc)$fatal(1,"TSTIO altered BC/HL/DE");
  if(EVENT&&frames!=1)$fatal(1,"TSTIO missing interrupt");passed=passed+1;
 end
 $display("PASS removed IO cases=%d stress=%d event=%d",passed,STRESS,EVENT);$finish;
 end
endmodule
