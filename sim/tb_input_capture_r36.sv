`timescale 1ns/1ps
// Simulation-only cutpoints isolate the exact wrapper input capture logic.
// Source selectors are forced; the captured input byte is never forced.
module tb_input_capture_r36;
 parameter DIAGNOSTIC_PROFILE=1;
 reg clk=0,fall=1;
 reg[7:0]din=0,trace=0,sel=0,mbase=0,signature=0;
 reg[23:0]addr=0;
 reg[2:0]ts=3,mc=2;
 reg io=0,wr=0,ic=1,ba=1,active=0,ext=0,madl=0;
 integer checks=0,captures=0,holds=0,valids=0,ev,av,sv,v,k,c;
 reg[7:0]previous;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(1'b0),.clk_enable(1'b0),.clk_falling(fall),.WAIT_n(1'b1),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),.Trace_Data(trace));
 G80A_eZ80_reference reference(.CLK_n(clk),.RESET_n(1'b0),.clk_enable(1'b0),.clk_falling(fall),.WAIT_n(1'b1),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),.Trace_Data(trace));
 initial begin
  force cpu.tstate=ts;force reference.tstate=ts;
  force cpu.mcycle=mc;force reference.mcycle=mc;
  force cpu.request_address=addr;force reference.request_address=addr;
  force cpu.request_io=io;force reference.request_io=io;
  force cpu.request_write=wr;force reference.request_write=wr;
  force cpu.intcycle_n=ic;force reference.intcycle_n=ic;
  force cpu.busak_n_i=ba;force reference.busak_n_i=ba;
  force cpu.diag_select=sel;force reference.diag_select=sel;
  force cpu.extension_state_i=ext;force reference.extension_state_i=ext;
  force cpu.mbase_i=mbase;force reference.mbase_i=mbase;
  force cpu.madl_i=madl;force reference.madl_i=madl;
 end
 generate if(DIAGNOSTIC_PROFILE)begin
  initial begin
   force cpu.diag_active=active;force reference.diag_active=active;
   force cpu.diag_io_signature=signature;force reference.diag_io_signature=signature;
  end
 end endgenerate
 task step;
  begin
   #1;previous=cpu.u0.di_reg;clk=1;#1;clk=0;#0.01;
   if(cpu.u0.di_reg!==reference.di_reg)
    $fatal(1,"input capture mismatch sel=%h din=%h req=%h",sel,din,addr);
   if(fall && ba && ts==3)begin
    if((^cpu.u0.di_reg)===1'bx)$fatal(1,"unknown captured byte");
    captures=captures+1;if(cpu.u0.di_reg[0])valids=valids+1;
   end else begin
    if(cpu.u0.di_reg!==previous)$fatal(1,"capture hold violated");
    holds=holds+1;
   end
   checks=checks+1;
  end
 endtask
 function dynamic_diag(input integer s);
  dynamic_diag=(s==8'hc8)||(s>=8'hf0 && s<=8'hf7)||s==8'hfa||s==8'hfd||s==8'hfe;
 endfunction
 initial begin
  // Every physical input byte, loopback byte and real IACK selector.
  for(c=0;c<4;c=c+1)begin
   for(v=0;v<256;v=v+1)begin
    ext=1;active=1;io=0;wr=0;ic=1;addr=0;mc=2;sel=v;din=v;mbase=v;trace=v;signature=v;
    case(c)
     1:begin addr=24'he7e7;io=1;end
     2:begin addr=((v^8'h5a)<<8)|8'he6;io=1;end
     3:begin ic=0;mc=1;end
    endcase
    step;
   end
  end
  // Every diagnostic selector; exhaust all possible bytes of each dynamic source.
  addr=24'he7e7;io=1;wr=0;ic=1;mc=2;
  for(ev=0;ev<2;ev=ev+1)for(av=0;av<2;av=av+1)for(sv=0;sv<256;sv=sv+1)begin
   ext=ev;active=av;sel=sv;
   for(v=0;v<((ev && dynamic_diag(sv))?256:1);v=v+1)begin
    mbase=v;trace=v;signature=v;madl=v&1;din=v^sv;step;
   end
  end
  // Writes, inactive diagnostics, wrong IACK cycle, non-I/O and full-address match.
  for(c=0;c<32;c=c+1)for(v=0;v<256;v=v+1)begin
   io=c[0];wr=c[1];ic=c[2];active=c[3];mc=c[4]?1:2;
   addr={8'h12,v[7:0],8'he6};sel=8'hc8;mbase=3;din=v;ext=1;step;
  end
  // Capture-enable, BUSACK and T-state gating: captured byte must hold.
  for(c=0;c<8;c=c+1)for(v=0;v<8;v=v+1)begin
   fall=c[0];ba=c[1];ts=c[2]?3:2;io=0;ic=1;din=v;step;
  end
  $display("PASS R36 input capture checks=%0d captures=%0d holds=%0d mode_bit_ones=%0d",checks,captures,holds,valids);$finish;
 end
endmodule
