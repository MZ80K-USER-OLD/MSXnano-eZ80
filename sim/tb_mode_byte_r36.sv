`timescale 1ns/1ps
// Isolate the real CPU frame_mode transition. Captured byte is never forced.
module tb_mode_byte_r36;
 parameter FAULT=0;
 reg clk=0,rst=0,ce=0,cf=0;
 reg[7:0]din=0;reg sl=0;
 integer s,v,checks=0;reg[2:0]expected_state;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(rst),.clk_enable(ce),.clk_falling(cf),.WAIT_n(1'b1),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),.Trace_Data(8'h00));
 initial begin
  force cpu.tstate=3'b011;force cpu.mcycle=3'b010;
  force cpu.busak_n_i=1'b1;force cpu.request_io=1'b0;
  force cpu.request_write=1'b0;force cpu.request_address=24'h050100;
 end
 task tick;begin #1;clk=1;#1;clk=0;#1;end endtask
 initial begin
  for(s=0;s<2;s=s+1)for(v=0;v<256;v=v+1)begin
   rst=0;ce=1;cf=0;tick;tick;rst=1;tick;tick;
   din=v;sl=s;
   force cpu.u0.frame_state=3'd3;
   force cpu.u0.frame_ts=3'd3;
   force cpu.u0.frame_start=1'b0;force cpu.u0.frame_end=1'b0;
   force cpu.u0.irq_im0=1'b0;
   force cpu.u0.spl=24'h050100;force cpu.u0.sp=16'hc000;
   force cpu.u0.mbase=8'h00;force cpu.u0.frame_count=2;
   if(FAULT==2)force cpu.u0.stream_long=1'b0;else force cpu.u0.stream_long=sl;
   ce=0;cf=1;tick;
   if(cpu.u0.di_reg!==v[7:0])$fatal(1,"mode byte capture mismatch");
   cf=0;ce=1;#1;clk=1;#0.01;
   release cpu.u0.frame_state;release cpu.u0.frame_ts;
   release cpu.u0.spl;release cpu.u0.sp;release cpu.u0.frame_count;
   if(FAULT==1)force cpu.u0.frame_mode_bit=1'b1;
   #0.01;
   expected_state=s?3'd4:(v[0]?3'd5:3'd6);
   if(cpu.u0.frame_state!==expected_state)$fatal(1,"return path mismatch byte=%h stream=%b actual=%h expected=%h",v[7:0],sl,cpu.u0.frame_state,expected_state);
   if(cpu.u0.frame_mode_bit!==v[0])$fatal(1,"saved mode bit mismatch");
   if(cpu.u0.spl!==24'h050101 || cpu.u0.frame_count!==0)$fatal(1,"mode frame stack update mismatch");
   if(s || v[0])begin
    if({cpu.u0.address_bank_reg,cpu.u0.address_reg}!==24'h050101)$fatal(1,"long frame address mismatch");
   end else if({cpu.u0.address_bank_reg,cpu.u0.address_reg}!==24'h00c000)$fatal(1,"short frame address mismatch");
   checks=checks+1;ce=0;clk=0;#1;
   release cpu.u0.frame_start;release cpu.u0.frame_end;release cpu.u0.irq_im0;release cpu.u0.mbase;release cpu.u0.stream_long;
  end
  $display("PASS R36 mode-bit-only cases=%0d",checks);$finish;
 end
endmodule
