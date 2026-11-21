`timescale 1ns/1ps
module tb_load_matrix_r24_2;
parameter STRESS=0;
reg clk=0,rst=0;always #10 clk=~clk;
reg[3:0]div=0;integer ticks=0;reg run=1;
always @(posedge clk)begin ticks<=ticks+1;if(!rst)begin div<=0;run<=1;end else if(div==(STRESS?14:3))begin div<=0;run<=!STRESS||ticks%257<180;end else div<=div+1;end
wire ce=div==0&&run,cf=div==(STRESS?7:2)&&run,wn=!STRESS||ticks%113<70;
reg[7:0]mem[0:1048575];wire[23:0]a;wire[15:0]msx;wire ext,mr,io,rf,rd,wr,m1,halt_n;wire[7:0]dout;
wire[7:0]din=(!mr&&!rd)?mem[a[19:0]]:8'hff;
G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(rst),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wn),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),.A24(a),.A_MSX(msx),.Extended_Window(ext),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
reg old_write=0;always @(posedge clk)if(rst)begin if(!mr&&!wr&&!old_write)mem[a[19:0]]<=dout;old_write<=!mr&&!wr;end
reg[23:0]p,base,addr,expected,actual,original;reg[7:0]pref,op;reg dl,sl,srcy;integer ci,family,target,pi,idx,d,k,passed=0;
task emit(input[7:0]v);begin mem[p[19:0]]=v;p=p+1;end endtask
task v24(input[23:0]v);begin emit(v[7:0]);emit(v[15:8]);emit(v[23:16]);end endtask
task pair(input[7:0]op,input[23:0]v);begin emit(op);v24(v);end endtask
initial begin
 for(ci=0;ci<68;ci=ci+1)begin
  rst=0;old_write=0;
  family=ci<24?0:ci<48?1:2;target=(ci-(family==0?0:family==1?24:48))/4;pi=ci%4;
  case(pi)0:pref=8'h40;1:pref=8'h49;2:pref=8'h52;3:pref=8'h5b;endcase
  dl=pref[3];sl=pref[4];srcy=pi[0];base=srcy?24'h0a7000:24'h0a6000;
  case(pi)0:d=-128;1:d=-1;2:d=0;3:d=127;endcase
  addr=family==2?base+d:24'h0a6000;
  mem[addr[19:0]]=8'h12;mem[(addr+1)&20'hfffff]=8'h34;mem[(addr+2)&20'hfffff]=8'h56;
  mem[addr[15:0]]=8'h12;mem[(addr[15:0]+1)&16'hffff]=8'h34;mem[(addr[15:0]+2)&16'hffff]=8'h56;
  p=0;emit(8'hc3);emit(0);emit(1);
  p=24'h100;emit(8'hf3);emit(8'h31);emit(0);emit(8'hf0);
  emit(1);emit(8'he7);emit(8'he7);emit(8'h3e);emit(8'ha5);emit(8'hed);emit(8'h79);emit(8'h3e);emit(8'h5a);emit(8'hed);emit(8'h79);
  emit(8'h5b);emit(8'hc3);v24(24'h0a1000);p=24'h0a1000;
  pair(8'h31,24'h050100);pair(1,24'h00a6d7);emit(8'h5b);emit(8'hc5);emit(8'h5b);emit(8'hf1);
  pair(1,24'h112233);pair(8'h11,24'h445566);pair(8'h21,24'h778899);
  emit(8'hdd);pair(8'h21,24'h0a6000);emit(8'hfd);pair(8'h21,24'h0a7000);
  emit(pref);
  if(family==0)begin
   case(target)0:op=1;1:op=8'h11;2:op=8'h21;3:begin emit(8'hdd);op=8'h21;end 4:begin emit(8'hfd);op=8'h21;end 5:op=8'h31;endcase
   emit(op);emit(8'h12);emit(8'h34);if(sl)emit(8'h56);
  end else if(family==1)begin
   case(target)0:begin emit(8'hed);op=8'h4b;end 1:begin emit(8'hed);op=8'h5b;end 2:op=8'h2a;3:begin emit(8'hdd);op=8'h2a;end 4:begin emit(8'hfd);op=8'h2a;end 5:begin emit(8'hed);op=8'h7b;end endcase
   emit(op);emit(0);emit(8'h60);if(sl)emit(8'h0a);
  end else begin
   emit(srcy?8'hfd:8'hdd);
   case(target)0:op=8'h07;1:op=8'h17;2:op=8'h27;3:op=srcy?8'h31:8'h37;4:op=srcy?8'h37:8'h31;endcase
   emit(op);emit(d[7:0]);
  end
  emit(8'h76);
  repeat(12)@(negedge clk);rst=1;k=0;
  while(halt_n!==0&&k<120000)begin @(negedge clk);k=k+1;end
  if(k>=120000)$fatal(1,"load matrix timeout case=%0d pc=%h",ci,cpu.u0.pc);
  case(target)0:begin idx=0;original=24'h112233;end 1:begin idx=1;original=24'h445566;end 2:begin idx=2;original=24'h778899;end 3:begin idx=3;original=24'h0a6000;end 4:begin idx=7;original=24'h0a7000;end default:begin idx=0;original=0;end endcase
  expected=dl?((family==0&&!sl)?24'h003412:24'h563412):((family==0&&sl)?24'h003412:{original[23:16],16'h3412});
  if(target==5)begin
   if(cpu.u0.sp!==(dl?16'hf000:16'h3412)||cpu.u0.spl!==(dl?expected:24'h050100))$fatal(1,"load SP mismatch case=%0d SP=%h SPL=%h expected=%h",ci,cpu.u0.sp,cpu.u0.spl,expected);
  end else begin
   actual={cpu.u0.regs.upper_view[63-idx*8-:8],cpu.u0.regs.regsh[idx],cpu.u0.regs.regsl[idx]};
   if(actual!==expected)$fatal(1,"load matrix mismatch case=%0d family=%0d target=%0d prefix=%h expected=%h actual=%h",ci,family,target,pref,expected,actual);
   if(cpu.u0.sp!==16'hf000||cpu.u0.spl!==24'h050100)$fatal(1,"load altered non-target stack pointer");
  end
  if(cpu.u0.f!==8'hd7||cpu.u0.acc!==8'ha6)$fatal(1,"load changed flags/A case=%0d F=%h A=%h",ci,cpu.u0.f,cpu.u0.acc);
  passed=passed+1;
 end
 $display("PASS load_matrix_r24_2 cases=%0d stress=%0d",passed,STRESS);$finish;
end
endmodule
