`timescale 1ns/1ps
module tb_timing_platform_r11_1;
 reg clk=0;always #5 clk=~clk;
 wire audio;wire clk_27m=clk;
 CLOCK_DIV #(.CLK_SRC(27),.CLK_DIV(0.044100),.PRECISION_BITS(16)) divider(.clk_src(clk),.clk_div(audio));
 integer tick=0,previous=-1,rises=0,minimum=9999,maximum=0;
 always @(posedge clk)tick=tick+1;
 always @(posedge audio)begin
  if(previous>=0)begin
   if(tick-previous<612||tick-previous>614)$fatal(1,"audio divider interval %d",tick-previous);
   if(tick-previous<minimum)minimum=tick-previous;
   if(tick-previous>maximum)maximum=tick-previous;
  end
  previous=tick;rises=rises+1;
 end
 reg bus_reset_n=1;
 reg [7:0] config1_ff=8'hfb;
 reg [6:0] config2_ff=7'h07;
 reg [1:0] config_mapper_slot_ff=3,config_sdcard_slot_ff=3;
 `include "config_initial_r11_1.vh"
 `include "config_capture_r11_1.vh"
 task check(input [1:0] mapper,sd,input m3,m12,en);
  if({config_mapper_slot_ff,config_sdcard_slot_ff,config_enable_mapper3,config_enable_mapper12,config_enable_sdcard}!=={mapper,sd,m3,m12,en})$fatal(1,"config capture mismatch");
 endtask
 initial begin
  #2;check(3,3,1,0,1);bus_reset_n=0;
  #24;check(3,3,1,0,1);
  @(negedge clk);config1_ff=8'h11;config2_ff=7'h02;
  @(negedge clk);check(1,1,0,1,0);bus_reset_n=1;
  config1_ff=8'h31;config2_ff=7'h07;
  repeat(5)@(negedge clk);check(1,1,0,1,0);
  bus_reset_n=0;@(negedge clk);check(3,3,1,0,1);bus_reset_n=1;
  repeat(200000)@(negedge clk);
  if(rises<300||minimum!=612||maximum<=612)$fatal(1,"fractional divider coverage");
  $display("PASS timing_platform_r11_1 config reset capture/hold and %d audio rises min=%d max=%d parent clocks",rises,minimum,maximum);$finish;
 end
endmodule
