`timescale 1ns/1ps
// Frame-state cutpoint: outside return-mode processing, input bytes must not
// change saved mode or stacks. Normal instruction execution is held here;
// instruction sequencing is covered separately by actual-COM differential tests.
module tb_frame_gate_r36;
 reg clk=0,rst=0,ce=0,cf=0;reg[7:0]din=0;
 integer g,v,checks=0;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(rst),.clk_enable(ce),.clk_falling(cf),.WAIT_n(1'b1),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),.Trace_Data(8'h00));
 initial begin
  force cpu.tstate=3'b011;force cpu.mcycle=3'b010;
  force cpu.busak_n_i=1'b1;force cpu.request_io=1'b0;
  force cpu.request_write=1'b0;force cpu.request_address=24'h050100;
 end
 task tick;begin #1;clk=1;#1;clk=0;#1;end endtask
 initial begin
  for(g=0;g<2;g=g+1)for(v=0;v<256;v=v+1)begin
   rst=0;ce=1;cf=0;tick;tick;rst=1;tick;tick;
   din=v;
   if(g==0)begin force cpu.u0.frame_state=3'd0;force cpu.u0.irq_im0=1'b0;end
   else begin force cpu.u0.frame_state=3'd3;force cpu.u0.irq_im0=1'b1;end
   force cpu.u0.frame_ts=3'd3;
   force cpu.u0.frame_start=1'b0;force cpu.u0.frame_end=1'b0;
   force cpu.u0.cpu_run=1'b0;
   force cpu.u0.spl=24'h050100;force cpu.u0.sp=16'hc000;
   ce=0;cf=1;tick;
   if(cpu.u0.di_reg!==v[7:0])$fatal(1,"gate test byte capture mismatch");
   cf=0;ce=1;#1;clk=1;#0.01;
   release cpu.u0.frame_state;release cpu.u0.spl;release cpu.u0.sp;
   #0.01;
   if(cpu.u0.frame_state!==3'd0)$fatal(1,"frame state changed outside return mode g=%d byte=%h",g,v);
   if(cpu.u0.frame_mode_bit!==1'b0 || cpu.u0.adl_mode!==1'b0)$fatal(1,"input byte interpreted as return mode outside context");
   if(cpu.u0.spl!==24'h050100 || cpu.u0.sp!==16'hc000)$fatal(1,"stack changed outside return mode");
   checks=checks+1;ce=0;clk=0;#1;
   release cpu.u0.frame_ts;release cpu.u0.frame_start;release cpu.u0.frame_end;
   release cpu.u0.cpu_run;release cpu.u0.irq_im0;
  end
  $display("PASS R36 frame-gate cases=%0d",checks);$finish;
 end
endmodule
