`timescale 1ns/1ps
module tb_io2_r21;
 parameter STRESS=0,EXTENDED=1,EVENT=0;
 reg clk=0,rst=0;always #10 clk=~clk;
 reg[3:0]div=0;integer ticks=0;reg run=1;
 always @(posedge clk)begin ticks<=ticks+1;if(!rst)begin div<=0;run<=1;end else if(div==(STRESS?14:3))begin div<=0;run<=!STRESS||ticks%257<180;end else div<=div+1;end
 wire ce=div==0&&run,cf=div==(STRESS?7:2)&&run,wn=!STRESS||ticks%113<70;
 reg[7:0]mem[0:1048575];wire[23:0]a;wire[15:0]msx;wire ext,mr,io,rf,rd,wr,m1,halt_n;wire[7:0]dout;
 reg irq=0,nmi=0;reg[7:0]input_data=0;
 wire[7:0]din=!io?(m1?input_data:8'hff):(!mr&&!rd?mem[a[19:0]]:8'hff);
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(rst),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wn),.INT_n(!irq),.NMI_n(!nmi),.BUSRQ_n(1'b1),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ext),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
 integer ci,k,opn,src,pi,passed=0,io_events=0,frames=0;reg[23:0]p,start,haltpc,afterio,target,hl0,hl1,bc0,bc1;
 reg[7:0]op,pref,b0,c0,f0,expect_f,data;reg wide,old_write=0,old_io=0,triggered=0,finished=0,old_frame=0;reg[31:0]held;reg holding=0;
 task emit(input[7:0]v);begin mem[p[19:0]]=v;p=p+1;end endtask
 task w24(input[23:0]v);begin emit(v[7:0]);emit(v[15:8]);emit(v[23:16]);end endtask
 task pair(input[7:0]opcode,input[23:0]v);begin emit(opcode);w24(v);end endtask
 always @(posedge clk)if(rst)begin
  if(!mr&&!wr&&!old_write)begin mem[a[19:0]]<=dout;if($test$plusargs("TRACE")&&ci==4)$display("WRITE a=%h d=%h pc=%h mc=%d ts=%d",a,dout,cpu.u0.pc,cpu.u0.mcycle,cpu.u0.tstate);end
  old_write<=!mr&&!wr;
  if(!io&&m1&&(!rd||!wr)&&cpu.u0.block_io2)begin
   if(!old_io)begin io_events=io_events+1;if($test$plusargs("TRACE")&&ci==4)$display("IO a=%h din=%h dataout=%h",a,din,dout);
    if(a!=={8'h00,b0,c0})$fatal(1,"port case=%d EXP=%h ACT=%h",ci,{8'h00,b0,c0},a);
    if(op[5]&&!wr&&dout!==data)$fatal(1,"OUT data case=%d EXP=%h ACT=%h",ci,data,dout);
   end
   if(holding&&held!=={a,dout})$fatal(1,"IO changed while active");held={a,dout};holding=1;
   if(EVENT&&!triggered)begin if(EVENT==1)irq<=1;else nmi<=1;triggered=1;end
  end else holding=0;
  old_io<=!io&&m1&&(!rd||!wr)&&cpu.u0.block_io2;
  if(!io&&!m1)irq<=0;
  if(ce&&cpu.u0.mcycle==6&&cpu.u0.t_res&&cpu.u0.ir==op)begin finished=1;if(cpu.u0.pc!==(src?afterio:{8'h00,afterio[15:0]}))$fatal(1,"IO2 consumed next opcode pc=%h expected=%h",cpu.u0.pc,afterio);end
  if(ce&&(cpu.u0.intcycle||cpu.u0.nmicycle)&&!old_frame)begin if(!finished)$fatal(1,"IRQ/NMI entered before IO2 complete");frames=frames+1;nmi<=0;end
  if(ce)old_frame<=cpu.u0.intcycle||cpu.u0.nmicycle;
 end
 initial begin
 for(ci=0;ci<(EXTENDED?40:4);ci=ci+1)begin
  rst=0;irq=0;nmi=0;old_io=0;old_write=0;holding=0;triggered=0;finished=0;old_frame=0;io_events=0;frames=0;
  opn=ci%4;src=(ci/4)%2;pi=(ci/8)%5;
  case(opn)0:op=8'h84;1:op=8'h8c;2:op=8'ha4;3:op=8'hac;endcase
  case(pi)0:pref=0;1:pref=8'h40;2:pref=8'h49;3:pref=8'h52;4:pref=8'h5b;endcase
  wide=pi==0?src:pref[3];b0=(ci%3==0)?1:(ci%3==1)?0:8'h80;c0=(ci%3==0)?8'hff:(ci%3==1)?0:8'he6;
  data=ci[0]?8'h80:8'h31;input_data=data;f0=ci[2]?8'hd7:8'h2a;
  bc0={8'h7a,b0,c0};bc1={8'h7a,8'(b0-1),8'(op[3]?c0-1:c0+1)};
  hl0=op[3]?24'h030000:24'h02ffff;hl1=wide?(op[3]?hl0-1:hl0+1):{hl0[23:16],16'(op[3]?hl0-1:hl0+1)};
  target=wide?hl0:{8'h0e,hl0[15:0]};mem[target[19:0]]=op[5]?data:~data;
  expect_f=(f0&8'hbd)|((8'(b0-1)==0)?8'h40:0)|(data[7]?2:0);
  p=0;emit(8'hc3);emit(0);emit(1);
  p=24'h100;emit(8'hf3);emit(8'h31);emit(0);emit(8'hf0);
  if(EXTENDED)begin emit(1);emit(8'he7);emit(8'he7);emit(8'h3e);emit(8'ha5);emit(8'hed);emit(8'h79);emit(8'h3e);emit(8'h5a);emit(8'hed);emit(8'h79);emit(8'h5b);emit(8'hc3);w24(24'h0a1000);p=24'h0a1000;
    pair(8'h31,24'h050100);pair(1,{8'h00,8'ha6,f0});emit(8'hc5);emit(8'hf1);pair(1,bc0);pair(8'h21,hl0);pair(8'h11,24'h13579b);emit(8'hdd);pair(8'h21,24'h2468ac);emit(8'hfd);pair(8'h21,24'h123456);
    emit(8'h3e);emit(14);emit(8'hed);emit(8'h6d);emit(8'h3e);emit(8'ha6);emit(8'hed);emit(8'h56);
    if(EVENT)begin emit(8'hfb);emit(0);end
    start=src?24'h0a2000:24'h0e8000;emit(src?8'h5b:8'h40);emit(8'hc3);emit(start[7:0]);emit(start[15:8]);if(src)emit(start[23:16]);p=start;
    if(pref)emit(pref);if(pi==1)emit(8'hdd);else if(pi==2)emit(8'hfd);emit(8'hed);emit(op);afterio=p;
    emit(8'hf3);emit(8'h5b);emit(8'hc5);emit(8'h5b);emit(8'he5);emit(8'h5b);emit(8'hf5);emit(8'h5b);emit(8'hd5);emit(8'h5b);emit(8'hdd);emit(8'he5);emit(8'h5b);emit(8'hfd);emit(8'he5);haltpc=p;emit(8'h76);
  end else begin emit(8'hed);emit(op);haltpc=p;emit(8'h76);end
  mem[24'h38]=8'hfb;mem[24'h39]=8'hed;mem[24'h3a]=8'h4d;
  mem[24'h66]=8'hed;mem[24'h67]=8'h45;
  mem[24'h0e0038]=8'hfb;mem[24'h0e0039]=8'hed;mem[24'h0e003a]=8'h4d;
  mem[24'h0e0066]=8'hed;mem[24'h0e0067]=8'h45;
  repeat(12)@(negedge clk);rst=1;k=0;
  while(halt_n!==0&&k<40000)begin @(negedge clk);k=k+1;end
  if(k>=40000)$fatal(1,"timeout case=%d pc=%h mc=%h ts=%h",ci,cpu.u0.pc,cpu.u0.mcycle,cpu.u0.tstate);
  if(io_events!=(EXTENDED?1:0))$fatal(1,"IO count case=%d count=%d",ci,io_events);
  if(EXTENDED)begin
   if({mem[20'h500ff],mem[20'h500fe],mem[20'h500fd]}!==bc1)$fatal(1,"BC case=%d EXP=%h ACT=%h",ci,bc1,{mem[20'h500ff],mem[20'h500fe],mem[20'h500fd]});
   if({mem[20'h500fc],mem[20'h500fb],mem[20'h500fa]}!==hl1)$fatal(1,"HL case=%d EXP=%h ACT=%h",ci,hl1,{mem[20'h500fc],mem[20'h500fb],mem[20'h500fa]});
   if(mem[20'h500f7]!==expect_f||mem[20'h500f8]!==8'ha6)$fatal(1,"AF case=%d EXP=%h ACT=%h A=%h",ci,expect_f,mem[20'h500f7],mem[20'h500f8]);
   if({mem[20'h500f6],mem[20'h500f5],mem[20'h500f4]}!==24'h13579b || {mem[20'h500f3],mem[20'h500f2],mem[20'h500f1]}!==24'h2468ac || {mem[20'h500f0],mem[20'h500ef],mem[20'h500ee]}!==24'h123456)$fatal(1,"DE/IX/IY changed case=%d",ci);
   if(cpu.u0.spl!==24'h0500ee||cpu.u0.sp!==16'hf000)$fatal(1,"stack changed case=%d",ci);
   if(!op[5]&&mem[target[19:0]]!==data)$fatal(1,"IN memory case=%d ADDR=%h EXP=%h ACT=%h",ci,target,data,mem[target[19:0]]);
   if(EVENT&&frames!=1)$fatal(1,"missing interrupt case=%d frames=%d",ci,frames);
  end
  passed=passed+1;
 end
 $display("PASS IO2 cases=%d stress=%d ext=%d event=%d",passed,STRESS,EXTENDED,EVENT);$finish;
 end
endmodule
