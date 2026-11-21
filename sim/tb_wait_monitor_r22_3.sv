`timescale 1ns/1ps
module tb_wait_monitor_r22_3;
 reg clk=0; always #5 clk=~clk;
 reg rst=0, button=0, mr=1,rd=1,wr=1,done=0,extwin=1;
 reg [23:0] addr=24'h010100;
 wire mm,xc,wn,req,rw; wire [15:0] ma; wire [22:0] ra;
 wire [7:0] di,wd; wire [4:0] bd; wire [63:0] trace;
 wire [5:0] leds; wire cap; wire [63:0] snap;
 ez80_memory_bridge #(.PREDECODED_MSX(1),.TRACE_MEMORY(1)) b(
 .clk(clk),.reset_n(rst),.cpu_addr(addr),.cpu_mreq_n(mr),.cpu_iorq_n(1'b1),
 .cpu_rfsh_n(1'b1),.cpu_rd_n(rd),.cpu_wr_n(wr),.cpu_dout(8'h31),
 .msx_mreq_n(mm),.msx_addr(ma),.extended_cycle(xc),.wait_n(wn),.cpu_din(di),
 .ram_req(req),.ram_write(rw),.ram_addr(ra),.ram_din(wd),.ram_done(done),
 .ram_dout(8'h31),.cpu_msx_addr(16'h0),.cpu_extended_window(extwin),
 .memory_trace(trace),.wait_debug(bd));
 ez80_wait_monitor #(.AGE_BITS(5),.DEBOUNCE_BITS(2),.DISPLAY_TICKS(5)) m(
 .clk(clk),.reset_n(rst),.button(button),.cpu_addr(addr),.ram_addr(ra),
 .mreq_n(mr),.rd_n(rd),.wr_n(wr),.extended_window(extwin),.wait_n(wn),
 .ram_req(req),.ram_write(rw),.ram_done(done),.wait_io(1'b1),
 .bridge_debug(bd),.controller_debug(4'h9),.led_n(leds),.captured(cap),.snapshot(snap));
 task tick(input integer n); repeat(n)begin @(posedge clk);#1;end endtask
 task reset; begin @(negedge clk);rst=0;mr=1;rd=1;wr=1;done=0;button=0;addr=24'h010100;extwin=1;tick(3);@(negedge clk);rst=1;tick(4);end endtask
 task start(input bit write);begin @(negedge clk);mr=0;rd=write;wr=!write;tick(3);end endtask
 task finish_cycle;begin @(negedge clk);done=1;tick(4);if(!wn)$fatal(1,"WAIT not released");@(negedge clk);mr=1;rd=1;wr=1;tick(2);@(negedge clk);done=0;tick(5);end endtask
 task expect_state(input [1:0] state);begin
 tick(40);if(!cap||snap[1:0]!==state)$fatal(1,"capture state expected=%d snapshot=%h",state,snap);
 if(snap[39:16]!==24'h010100||snap[15:12]!==4'h9)$fatal(1,"payload/CDC wrong");
 end endtask
 reg [63:0] saved;
 integer page;
 initial begin
 reset;tick(100);if(cap)$fatal(1,"internal cycle false capture");
 start(1);finish_cycle;start(0);finish_cycle;tick(40);
 if(cap||di!==8'hff||b.state!==0)$fatal(1,"normal handshake changed");
 $display("PASS normal write/read and non-MREQ internal cycle");
 reset;@(negedge clk);mr=0;expect_state(0);
 if(snap[3:2]!==0||snap[5]!==0)$fatal(1,"IDLE request classification");
 $display("PASS no RD/WR request capture %h",snap);
 reset;start(0);expect_state(1);
 if(snap[3:2]!==1||snap[5]!==0||snap[62:40]!==23'h650100)$fatal(1,"WAIT_RAM capture");
 $display("PASS missing ACK capture %h",snap);
 saved=snap;finish_cycle;addr=24'habcdef;tick(40);if(snap!==saved)$fatal(1,"snapshot not sticky");
 // All 16 pages, index/data polarity, bounce rejection and wrap. No CPU clock involved.
 for(page=0;page<16;page=page+1)begin
 tick(6);if(leds!==~{2'b11,4'((saved>>(4*page))&15)})$fatal(1,"LED data page %d got %b",page,leds);
 @(negedge clk);button=1;tick(1);@(negedge clk);button=0;tick(8);
 if(m.page!==page[3:0])$fatal(1,"button bounce advanced page");
 @(negedge clk);button=1;tick(7);
 if(m.page!==4'((page+1)%16)||leds[4]!==1'b1)$fatal(1,"page/index display");
 tick(20);if(m.page!==4'((page+1)%16))$fatal(1,"held button repeats");
 @(negedge clk);button=0;tick(8);
 end
 $display("PASS frozen snapshot, 16 LED pages, debounce, held-button and wrap");
 reset;start(1);@(negedge clk);done=1;tick(4);@(negedge clk);mr=1;rd=1;wr=1;tick(3);
 if(b.state!==3)$fatal(1,"no DRAIN");start(0);expect_state(3);
 if(snap[3:2]!==2'b10||snap[7:6]!==2'b11)$fatal(1,"stale ACK capture");
 $display("PASS stale previous ACK DRAIN capture %h",snap);
 reset;start(0);@(negedge clk);done=1;expect_state(2);
 if(snap[5]!==1)$fatal(1,"COMPLETE WAIT high not captured");
 $display("PASS COMPLETE held MREQ capture %h",snap);
 reset;addr=24'hfe0100;start(0);tick(60);if(cap)$fatal(1,"unmapped false capture");
 reset;extwin=0;start(0);tick(60);if(cap)$fatal(1,"MSX false capture");
 $display("PASS unmapped and MSX cycles excluded");
 reset;if(cap||snap!==0)$fatal(1,"reset did not clear latch");
 $display("PASS wait monitor R22.3");$finish;
 end
 initial begin #100000;$fatal(1,"test timeout");end
endmodule
