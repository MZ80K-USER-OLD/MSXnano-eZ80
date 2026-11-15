`timescale 1ns/1ps
`default_nettype none
module tb_legacy_snapshot_r20_5;
 parameter PHASE=0,POISON=0,RESET_CASE=0,LAUNCH_NEG=0;
 reg c108=0,c54=0,c27=0,rst=0;always #5 c108=~c108;always #10 c54=~c54;always #20 c27=~c27;
 reg[1:0]dot=0;reg dh=0,dl=0;
 always @(posedge c27)if(!rst)begin dot<=0;dh<=0;dl<=0;end else begin
 dot<={dot[0],!dot[1]};case(dot)0:begin dh<=0;dl<=1;end 1:begin dh<=1;dl<=0;end 3:begin dh<=0;dl<=0;end 2:begin dh<=1;dl<=1;end endcase end
 reg mr=0,mw=0,gr=0,gw=0;reg[21:0]ma=0;reg[20:0]ga=0;reg[7:0]din=0;
 wire[7:0]md,gd;reg er=0,ew=0;reg[22:0]ea=0;reg[7:0]ed=0;wire done;wire[7:0]eo;
 wire[3:0]cmd,dm;wire[10:0]sa;wire[1:0]ba;wire[31:0]dq;
 memory_ctrl_ez80 #(.SLEEP_REFRESH(1)) mem(.clk_27m(c54),.clk_108m(c108),.bus_reset_n(rst),.video_dhclk(dh),.video_dlclk(dl),
 .mapper_req(mr),.mapper_write(mw),.mapper_addr(ma),.mapper_din(din),.mapper_dout(md),
 .megaram_req(gr),.megaram_write(gw),.megaram_addr(ga),.megaram_dout(gd),
 .vram_addr(17'b0),.vram_write(1'b0),.vram_din(8'b0),.bus_rfsh_n(1'b1),.cpu_sleep(1'b0),
 .ext_req(er),.ext_write(ew),.ext_addr(ea),.ext_din(ed),.ext_done(done),.ext_dout(eo),
 .O_sdram_cs_n(cmd[3]),.O_sdram_ras_n(cmd[2]),.O_sdram_cas_n(cmd[1]),.O_sdram_wen_n(cmd[0]),.O_sdram_dqm(dm),.O_sdram_addr(sa),.O_sdram_ba(ba),.IO_sdram_dq(dq));
 sdram_model33 ram(c108,cmd,sa,ba,dm,dq);
 integer count=0,vreads=0,i,j,n;time started,max_latency=0;reg[22:0]helda;reg[7:0]heldd;reg heldowner;
 always @(posedge c108)if(rst&&cmd==4'b0101&&ba==3)vreads=vreads+1;
 task legacy(input bit mega,input bit write,input[21:0]a,input[7:0]d,input[7:0]expected);
 begin
  wait(mem.sdram_seq==0);repeat((count*5+PHASE)%8)@(posedge c54);if(LAUNCH_NEG)@(negedge c54);else @(posedge c54);#1;started=$time;ma=a;ga=a[20:0];din=d;mw=write;gw=write;mr=!mega;gr=mega;
  wait(mem.sdram_seq==1);#1;helda=mem.sdram_addr;heldd=mem.sdram_din_latched;heldowner=mem.sdram_mapper_latched;
  if(POISON)begin ma=22'h3abcdf;ga=21'h123456;din=~d;mw=0;gw=0;end
  while(mem.sdram_seq!=4)begin @(posedge c54);#1;
    if(mem.sdram_addr!==helda||mem.sdram_din_latched!==heldd||mem.sdram_mapper_latched!==heldowner)$fatal(1,"payload changed while accepted");
  end
  if($time-started>max_latency)max_latency=$time-started;
  if(!write&&(mega?gd:md)!==expected)$fatal(1,"legacy read ADDR=%h EXP=%h ACT=%h",a,expected,(mega?gd:md));
  @(posedge c54);#1;mr=0;gr=0;mw=0;gw=0;wait(mem.sdram_seq==0);count=count+1;
 end endtask
 task extended_read(input[22:0]a,input[7:0]expected);
 begin
  @(posedge c54);#1;ea=a;ew=0;er=1;n=0;
  while(!done&&n<3000)begin @(posedge c54);#1;n=n+1;end
  if(!done)$fatal(1,"extended verify timeout");
  if(eo!==expected)$fatal(1,"snapshot write ADDR=%h EXP=%h ACT=%h",a,expected,eo);
  er=0;wait(!done);repeat(4)@(posedge c54);
 end endtask
 initial begin
  repeat(12)@(negedge c54);rst=1;@(negedge c108);mem.RstSeq=24;mem.ff_mem_seq=0;mem.ff_sdr_seq=0;mem.SdrSta=0;
  repeat(50+PHASE)@(posedge c54);
  for(i=0;i<16;i=i+1)begin
   legacy(0,1,22'h006000+i,8'h31+i,0);extended_read(23'h006000+i,8'h31+i);
   legacy(0,0,22'h006000+i,0,8'h31+i);
   legacy(1,1,22'h001ffc+i,8'ha1+i,0);extended_read(23'h401ffc+i,8'ha1+i);
   legacy(1,0,22'h001ffc+i,0,8'ha1+i);
  end
  // Both legacy request lines asserted: mapper owns the accepted payload.
  @(posedge c54);#1;ma=22'h007000;ga=21'h003000;din=8'h5a;mw=1;gw=1;mr=1;gr=1;
  wait(mem.sdram_seq==4);#1;mr=0;gr=0;mw=0;gw=0;wait(mem.sdram_seq==0);extended_read(23'h007000,8'h5a);
  if(RESET_CASE)begin
   @(posedge c54);#1;mr=1;mw=1;ma=22'h006004;din=8'hdd;wait(mem.sdram_seq==1);#1;rst=0;mr=0;mw=0;
   repeat(4)@(posedge c54);#1;
   if(mem.legacy_snapshot_valid!==0||mem.sdram_seq!==0)$fatal(1,"reset retained accepted request");
   @(negedge c54);rst=1;@(negedge c108);mem.RstSeq=24;mem.ff_mem_seq=0;mem.ff_sdr_seq=0;mem.SdrSta=0;
   repeat(50)@(posedge c54);legacy(0,1,22'h006004,8'h3e,0);extended_read(23'h006004,8'h3e);
  end
  if(max_latency>=300)$fatal(1,"model service exceeds one divide-by-30 CPU period latency=%0d",max_latency);
  if(vreads<1||count!=64+RESET_CASE)$fatal(1,"coverage transactions=%0d video_reads=%0d",count,vreads);
  $display("PASS legacy_snapshot phase=%0d poison=%0d reset=%0d launch_neg=%0d transactions=%0d VDP_reads=%0d max_latency_ns=%0d",PHASE,POISON,RESET_CASE,LAUNCH_NEG,count,vreads,max_latency);$finish;
 end
 initial begin #5000000;$fatal(1,"snapshot timeout seq=%d",mem.sdram_seq);end
endmodule
`default_nettype wire
