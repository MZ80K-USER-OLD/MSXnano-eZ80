`timescale 1ns/1ps
module tb_refresh_r20_1;
 parameter PHASE=0,LONG_RUN=0,FAULT=0;
 reg c108=0,c54=0,c27=0,rst=0;always #5 c108=~c108;always #10 c54=~c54;always #20 c27=~c27;
 reg[1:0]dot=0;reg dh=0,dl=0;
 always @(posedge c27)if(!rst)begin dot<=0;dh<=0;dl<=0;end else begin
 dot<={dot[0],!dot[1]};case(dot)0:begin dh<=0;dl<=1;end 1:begin dh<=1;dl<=0;end 3:begin dh<=0;dl<=0;end 2:begin dh<=1;dl<=1;end endcase end
 reg slp=0,req=0,write=0;reg[22:0]addr=0;reg[7:0]din=0;wire done;wire[7:0]dout;wire[3:0]cmd,dm;wire[10:0]sa;wire[1:0]ba;wire[31:0]dq;wire timer;
 memory_ctrl_ez80 #(.SLEEP_REFRESH(1)) mem(.clk_27m(c54),.clk_108m(c108),.bus_reset_n(rst),.video_dhclk(dh),.video_dlclk(dl),.mapper_req(1'b0),.mapper_write(1'b0),.mapper_addr(22'b0),.mapper_din(8'b0),.megaram_req(1'b0),.megaram_write(1'b0),.megaram_addr(21'b0),.vram_addr(17'b0),.vram_write(1'b0),.vram_din(8'b0),.bus_rfsh_n(1'b1),.cpu_sleep(slp),.sleep_timer(timer),.ext_req(req),.ext_write(write),.ext_addr(addr),.ext_din(din),.ext_done(done),.ext_dout(dout),.O_sdram_cs_n(cmd[3]),.O_sdram_ras_n(cmd[2]),.O_sdram_cas_n(cmd[1]),.O_sdram_wen_n(cmd[0]),.O_sdram_dqm(dm),.O_sdram_addr(sa),.O_sdram_ba(ba),.IO_sdram_dq(dq));
 sdram_model33 ram(c108,cmd,sa,ba,dm,dq);
 integer refs=0,vreads=0,acks=0,ticks=0,lastref=0,gap=0,i,j,n=0;integer hist[0:4095];reg checking=0;reg olddone=0,oldcmd=0;reg[23:0]tag;
 always @(posedge c108)begin
 ticks=ticks+1;
 if(checking)begin
  if(mem.sleep_refresh_slot&&mem.ff_sdr_seq==7&&!dl)$fatal(1,"refresh stole VDP slot");
  if(cmd==4'b0101&&ba==3)vreads=vreads+1;
  if(cmd==4'b0001&&!oldcmd)begin
   if(dl)$fatal(1,"autonomous refresh in VDP slot");
   if(lastref!=0)begin if(ticks-lastref>gap)gap=ticks-lastref;if(ticks-lastref>1562)$fatal(1,"REFRESH interval exceeds 15.625us gap=%0d",ticks-lastref);end
   if(refs>=4096&&ticks-hist[refs%4096]>6400000)$fatal(1,"REFRESH fewer than 4096/64ms");
   hist[refs%4096]=ticks;lastref=ticks;refs=refs+1;
  end
  if(lastref!=0&&ticks-lastref>1562)$fatal(1,"REFRESH stopped");
  if(done&&!olddone)acks=acks+1;
 end
 olddone<=done;oldcmd<=cmd==4'b0001;
 end
 task transaction(input integer w,input[22:0]a,input[7:0]d,input[7:0]exp);
 begin
 @(negedge c54);addr=a;write=w;din=d;req=1;n=0;
 while(!done&&n<2000)begin @(negedge c54);n=n+1;end
 if(!done)$fatal(1,"refresh/CPU deadlock");if(!w&&dout!==exp)$fatal(1,"data ADDR=%h EXP=%h ACT=%h",a,exp,dout);
 repeat(4)@(negedge c54);req=0;wait(!done);repeat(4)@(negedge c54);
 end endtask
 initial begin
 repeat(12)@(negedge c54);rst=1;@(negedge c108);mem.RstSeq=24;mem.FreeCounter=PHASE*17;repeat(PHASE)@(negedge c54);repeat(50)@(negedge c54);
 // All four banks and all byte lanes, including the VDP's bank-3 row 0.
 for(i=0;i<4;i=i+1)for(j=0;j<4;j=j+1)transaction(1,(i<<21)+j,8'h11+i*16+j,0);
 checking=1;slp=1;
 if(FAULT)force mem.sleep_refresh_pending=0;
 for(i=0;i<64;i=i+1)begin
 transaction(1,23'h700000+i,8'h31+i,0);transaction(0,23'h700000+i,0,8'h31+i);
 end
 if(FAULT)begin repeat(3000)@(negedge c108);if(refs==0)$fatal(1,"REFRESH missing autonomous commands");end
 wait(refs>=(LONG_RUN?8192:128));
 for(i=0;i<4;i=i+1)for(j=0;j<4;j=j+1)transaction(0,(i<<21)+j,0,8'h11+i*16+j);
 if(mem.vram_dout!==16'h4241)$fatal(1,"VDP data/priority wrong %h",mem.vram_dout);
 if(vreads<refs||acks!=144)$fatal(1,"refresh coverage refs=%0d vreads=%0d acks=%0d",refs,vreads,acks);
 slp=0;checking=0;repeat(100)@(negedge c108);
 $display("PASS refresh phase=%0d long=%0d refreshes=%0d max_gap_10ns=%0d VDP_reads=%0d",PHASE,LONG_RUN,refs,gap,vreads);$finish;
 end
 initial begin #150000000;$fatal(1,"refresh timeout refs=%0d",refs);end
endmodule
