`timescale 1ns/1ps
// Simulation-only fault injection. Production RTL is unchanged.
module tb_block_faults_r33;
 parameter KIND=0;
 tb_differential_r27 #(.CPU_DIV(4)) dut();
 initial begin
  if(KIND==0) force dut.cpu.u0.pair_low_wrap=1'b0;
  else force dut.cpu.u0.block_result_zero=1'b0;
 end
endmodule
