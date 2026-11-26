`timescale 1ns/1ps
module tb_input_frame_r29;
reg clk=0,rst=0,cf=0,waitn=0,busak=1;
reg [2:0] ts=3,mc=2;reg io=0,wr=0,ic=1;
reg [23:0] addr=24'he100;reg [7:0] data=0,db=0;
reg [7:0] saved;integer b,s,h,j,checks=0;
G80A_eZ80 dut(.RESET_n(rst),.CLK_n(clk),.clk_enable(1'b0),.clk_falling(cf),.WAIT_n(waitn),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(data));
always #10 clk=~clk;
task check;input[7:0] exp;reg valid;begin
 #0.01;valid=(exp==8'h02 || exp==8'h03);
 if(dut.di_reg!==exp || dut.di_frame_valid_reg!==valid || dut.u0.frame_byte_valid!==valid)
 $fatal(1,"input/frame mismatch b=%h src=%d ts=%h cf=%b busak=%b wait=%b data=%h valid=%b",exp,s,ts,cf,busak,waitn,dut.di_reg,dut.di_frame_valid_reg);
 checks=checks+1;
end endtask
initial begin
 force dut.reset_s=rst;force dut.tstate=ts;force dut.mcycle=mc;
 force dut.request_address=addr;force dut.request_io=io;force dut.request_write=wr;
 force dut.intcycle_n=ic;force dut.busak_n_i=busak;
 force dut.diag_active=1'b1;force dut.diag_read=db;force dut.diag_iack_byte=db;
 repeat(3)@(negedge clk);#0.1;rst=1;cf=1;
 for(b=0;b<256;b=b+1)for(s=0;s<4;s=s+1)for(h=0;h<2;h=h+1)begin
  @(posedge clk);#0.1;ts=3;busak=1;cf=1;waitn=h;data=b;db=b;mc=2;ic=1;wr=0;
  case(s)
   0:begin addr=24'he100;io=0;end
   1:begin addr=24'he7e7;io=1;end
   2:begin addr={8'h00,(8'(b)^8'h5a),8'he6};io=1;end
   3:begin addr=24'he100;io=0;mc=1;ic=0;end
  endcase
  @(negedge clk);check(b);saved=b;
  for(j=0;j<3;j=j+1)begin
   @(posedge clk);#0.1;data=~b;db=~b;
   cf=(j!=0);ts=(j==1?2:3);busak=(j!=2);
   @(negedge clk);check(saved);
  end
 end
 $display("PASS R29 input/frame checks=%0d captures=2048 holds=6144",checks);$finish;
end
initial begin #10000000;$fatal(1,"input/frame timeout");end
endmodule
