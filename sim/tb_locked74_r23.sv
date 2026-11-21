`timescale 1ns/1ps
module tb_locked74_r23;
 reg clk=0,rst=0;always #10 clk=~clk;
 reg[1:0]div=0;always @(posedge clk)div<=div+1'b1;
 reg[7:0]mem[0:65535];wire[23:0]a;wire mr,rd,halt_n;wire[7:0]dout;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(rst),.clk_enable(div==0),.clk_falling(div==2),.WAIT_n(1'b1),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(!mr&&!rd?mem[a[15:0]]:8'hff),.A24(a),.MREQ_n(mr),.RD_n(rd),.DO(dout),.HALT_n(halt_n));
 initial begin
  mem[0]=8'hf3;mem[1]=8'h31;mem[2]=0;mem[3]=8'hf0;mem[4]=8'h3e;mem[5]=8'ha6;mem[6]=8'hed;mem[7]=8'h74;mem[8]=8'h76;
  repeat(12)@(negedge clk);rst=1;
  wait(halt_n==0);#1;
  if(cpu.u0.acc!==8'h5a||(cpu.u0.f&8'hd7)!==8'h13||cpu.u0.extensions_enabled!==0)$fatal(1,"locked ED74 NEG alias changed A=%h F=%h",cpu.u0.acc,cpu.u0.f);
  $display("PASS locked ED74 NEG alias");$finish;
 end
 initial begin #200000;$fatal(1,"locked ED74 timeout");end
endmodule
