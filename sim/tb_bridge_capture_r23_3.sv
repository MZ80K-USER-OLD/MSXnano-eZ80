`timescale 1ns/1ps
module tb_bridge_capture_r23_3;
 reg clk=0,rst=0;always #10 clk=~clk;
 reg[23:0]a=0;reg mr=1,rd=1,wr=1,window=0;reg[7:0]d=0,ret=0;reg done=0;
 wire req,rw,wn,ext,mm;wire[22:0]ra;wire[7:0]wd,di;wire[15:0]ma;wire[63:0]trace_bus;
 ez80_memory_bridge #(.REQUEST_BANK_QUALIFIED(1),.PREDECODED_MSX(1),.TRACE_MEMORY(1)) dut(
 .clk(clk),.reset_n(rst),.cpu_addr(a),.cpu_mreq_n(mr),.cpu_iorq_n(1'b1),.cpu_rfsh_n(1'b1),
 .cpu_rd_n(rd),.cpu_wr_n(wr),.cpu_dout(d),.cpu_msx_addr(16'h0),.cpu_extended_window(window),
 .msx_mreq_n(mm),.msx_addr(ma),.extended_cycle(ext),.wait_n(wn),.cpu_din(di),
 .ram_req(req),.ram_write(rw),.ram_addr(ra),.ram_din(wd),.ram_done(done),.ram_dout(ret),.memory_trace(trace_bus));
 integer i,k,op,phase,cases=0;reg[23:0]logical;reg[22:0]physical;reg[7:0]value;
 task tick;begin @(posedge clk);#1;end endtask
 task idle;begin @(negedge clk);mr=1;rd=1;wr=1;window=0;done=0;repeat(6)tick;if(req)$fatal(1,"not drained");end endtask
 initial begin
 repeat(3)tick;rst=1;idle;
 // No memory request, including long internal / idle time: no WAIT or request.
 window=1;a=24'h07fffe;
 repeat(4096)begin tick;if(req||!wn)$fatal(1,"idle/NoMREQ falsely waits");end
 for(i=0;i<8;i=i+1)for(op=0;op<2;op=op+1)for(phase=1;phase<=9;phase=phase+4)begin
 case(i)0:logical=24'h010100;1:logical=24'h07fffe;2:logical=24'h07ffff;3:logical=24'h080000;
 4:logical=24'h0a6000;5:logical=24'h010101;6:logical=24'h010102;7:logical=24'h010103;endcase
 physical=23'h640000+logical;value=op?8'h31:8'hce;
 @(negedge clk);a=logical;window=1;mr=0;rd=1;wr=1;d=8'he7;
 #1;if(wn)$fatal(1,"WAIT not early in T1");
 repeat(3)begin tick;if(req||wn)$fatal(1,"T1 prematurely accepted or lost WAIT");end
 @(negedge clk);#(phase);if(op)wr=0;else rd=0;
 tick;if(req||wn)$fatal(1,"request before sampled control");
 // Data may settle after the local strobe sample, before actual capture.
 #2;d=value;
 tick;if(!req||wn||ra!==physical||wd!==value||rw!==op[0])$fatal(1,"capture a=%h data=%h",ra,wd);
 if(op&&trace_bus[30:0]!=={physical,value})$fatal(1,"trace uses different acceptance");
 repeat(12)begin tick;if(!req||wn||ra!==physical||wd!==value||rw!==op[0])$fatal(1,"payload changed under WAIT");end
 @(negedge clk);ret=8'ha5;done=1;k=0;
 while(!wn&&k<10)begin tick;k=k+1;end
 if(!wn||req||di!==8'ha5)$fatal(1,"bad completion");
 repeat(12)begin tick;if(req||!wn)$fatal(1,"duplicate/early WAIT");end
 // New request starts while old done remains high: must drain, not duplicate.
 @(negedge clk);mr=1;rd=1;wr=1;tick;
 @(negedge clk);mr=0;rd=0;wr=1;d=8'h42;
 repeat(3)begin tick;if(req||wn)$fatal(1,"accepted while old done high");end
 @(negedge clk);done=0;k=0;
 while(!req&&k<12)begin tick;k=k+1;end
 if(!req||wn||rw!==0||ra!==physical)$fatal(1,"back-to-back not accepted");
 @(negedge clk);done=1;ret=8'h5a;k=0;
 while(!wn&&k<10)begin tick;k=k+1;end
 if(!wn||req||di!==8'h5a)$fatal(1,"back-to-back completion");
 idle;cases=cases+1;
 end
 // Withdrawal after sampling but before capture must not issue a stale request.
 @(negedge clk);a=24'h010100;window=1;mr=0;wr=0;rd=1;tick;
 @(negedge clk);mr=1;wr=1;repeat(5)begin tick;if(req||!wn)$fatal(1,"stale sampled request");end
 idle;
 // Reset clears an outstanding request and all sampled qualifiers.
 @(negedge clk);a=24'h010100;window=1;mr=0;wr=0;rd=1;repeat(3)tick;
 if(!req)$fatal(1,"reset setup");@(negedge clk);rst=0;mr=1;wr=1;window=0;tick;
 if(req||!wn)$fatal(1,"reset failed");rst=1;repeat(8)begin tick;if(req)$fatal(1,"reset replayed stale request");end
 $display("PASS capture phases cases=%0d + idle/drain/cancellation/reset",cases);$finish;
 end
 initial begin #10000000;$fatal(1,"protocol timeout");end
endmodule
