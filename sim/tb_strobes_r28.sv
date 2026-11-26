`timescale 1ns/1ps
module tb_strobes_r28;
reg clk=0,rst=0,cf=0;always #10 clk=~clk;
reg [2:0] mc=1,ts=1;reg nr=0,w=0,io=0,ic=1;
wire [3:0] dutbus,refbus;integer a,b,c,k,checks=0;
G80A_eZ80 dut(.RESET_n(rst),.CLK_n(clk),.clk_enable(1'b0),.clk_falling(cf),.WAIT_n(1'b0),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(8'h00),.RD_n(dutbus[0]),.WR_n(dutbus[1]),.MREQ_n(dutbus[2]),.IORQ_n(dutbus[3]));
G80A_eZ80_reference refcpu(.RESET_n(rst),.CLK_n(clk),.clk_enable(1'b0),.clk_falling(cf),.WAIT_n(1'b0),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(8'h00),.RD_n(refbus[0]),.WR_n(refbus[1]),.MREQ_n(refbus[2]),.IORQ_n(refbus[3]));
task compare;begin #0.002;if(dutbus!==refbus)$fatal(1,"strobe mismatch MC=%h TS=%h NR/W/IO/IC=%b%b%b%b got=%b expected=%b",mc,ts,nr,w,io,ic,dutbus,refbus);checks=checks+1;end endtask
initial begin
 force dut.reset_s=rst;force refcpu.reset_s=rst;
 force dut.mcycle=mc;force refcpu.mcycle=mc;force dut.tstate=ts;force refcpu.tstate=ts;
 force dut.noread=nr;force refcpu.noread=nr;force dut.write=w;force refcpu.write=w;
 force dut.iorq=io;force refcpu.iorq=io;force dut.intcycle_n=ic;force refcpu.intcycle_n=ic;
 force dut.request_write=w;force refcpu.request_write=w;
 force dut.busak_n_i=1'b1;force refcpu.busak_n_i=1'b1;
 force dut.ireq_inhibit=1'b0;force refcpu.ireq_inhibit=1'b0;
 force dut.req_inhibit=1'b0;force refcpu.req_inhibit=1'b0;
 force dut.mreq_inhibit=1'b0;force refcpu.mreq_inhibit=1'b0;
 repeat(3)@(negedge clk);#0.1;rst=1;cf=1;
 for(a=0;a<8;a=a+1)for(b=0;b<8;b=b+1)for(c=0;c<16;c=c+1)begin
  @(negedge clk);#0.1;mc=a;ts=b;{nr,w,io,ic}=c;
  repeat(3)begin @(negedge clk);compare;end
  // Pause the qualified falling edge while the preparation stage continues.
  #0.1;cf=0;
  repeat(2)begin @(negedge clk);compare;end
  #0.1;cf=1;
 end
 @(negedge clk);#0.1;rst=0;#0.1;compare;
 $display("PASS R28 strobe matrix checks=%0d combinations=1024",checks);$finish;
end
initial begin #10000000;$fatal(1,"strobe matrix timeout");end
endmodule
