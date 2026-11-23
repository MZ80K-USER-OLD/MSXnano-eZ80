`timescale 1ns/1ps
module tb_uart_profiles_r24_5;
parameter DIAGNOSTIC=0;
localparam BIT_CLOCKS=234;
reg clk=0;always #18.5185 clk=~clk;
reg reset_n=0,send=0,ce=1,mr=1,io=1,rd=1,wr=1;
reg[15:0]addr=0;reg[7:0]data=0;
wire tx,boot;
msx2p_debug dut(.clk_27m(clk),.clk(clk),.clk_enable(ce),.reset_n(reset_n),
 .bus_addr(addr),.bus_data(data),.bus_mreq_n(mr),.bus_iorq_n(io),
 .bus_rd_n(rd),.bus_wr_n(wr),.send(send),.uart_tx(tx),.boot_ok(boot));
integer ticks=0,received=0;
reg[47:0]text=0;
reg[7:0]ch;
always @(posedge clk)begin
 ticks<=ticks+1;
 if(!DIAGNOSTIC)begin
  #1;if(tx!==1'b1||boot!==1'b0)$fatal(1,"normal GPRJ did not select inactive UART");
 end
end
generate if(DIAGNOSTIC)begin:diag
 initial begin
  repeat(49990)@(posedge clk);
  $display("UART_DIAG sender=%0d print=%0d head=%0d tail=%0d received=%0d text=%h",dut.send_state,dut.print_state,dut.seq_head,dut.seq_tail,received,text);
 end
 initial begin
  // Accelerate only the 100ms log scheduler. The UART baud divider and
  // character-generation pipeline run unchanged from production sources.
  force dut.tic=1'b0;
  wait(reset_n);repeat(10)@(negedge clk);send=1;
  force dut.tic=1'b1;@(negedge clk);force dut.tic=1'b0;
  repeat(20)@(negedge clk);
  force dut.tic=1'b1;@(negedge clk);force dut.tic=1'b0;
 end
 initial forever begin
  @(negedge tx);
  repeat(BIT_CLOCKS/2)@(posedge clk);
  if(tx!==0)$fatal(1,"UART start bit invalid");
  for(integer bitno=0;bitno<8;bitno=bitno+1)begin
   repeat(BIT_CLOCKS)@(posedge clk);ch[bitno]=tx;
  end
  repeat(BIT_CLOCKS)@(posedge clk);
  if(tx!==1)$fatal(1,"UART stop bit invalid");
  text={text[39:0],ch};received=received+1;
  if(received==6)begin
   if(text!=="state=")$fatal(1,"UART log prefix mismatch: %h",text);
   $display("PASS UART diagnostic: decoded state= at the production baud divider");$finish;
  end
 end
end endgenerate
initial begin
 repeat(5)@(negedge clk);reset_n=1;
 for(integer n=0;n<50000;n=n+1)begin
  @(negedge clk);addr=n*17;data=n;mr=n[0];io=n[1];wr=n[2];rd=n[3];ce=n[4];
  if(!DIAGNOSTIC)send=n[5];
 end
 if(DIAGNOSTIC)$fatal(1,"UART diagnostic produced no complete log");
 $display("PASS UART normal: idle TX under reset/bus/send activity");$finish;
end
endmodule
