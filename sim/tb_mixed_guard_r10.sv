`timescale 1ns/1ps
// CPU bus unit fixture: synthetic ROM covers all 24 bits, unlike board SDRAM mapping.
module tb_mixed_guard_r10;
 parameter TARGET_ADL=1,STRESS=0,GUARD=-1;
 reg clk=0,reset_n=0;always #10 clk=~clk;
 integer ticks=0;reg [3:0] divider=0;reg enable_run=1;
 always @(posedge clk) begin
  ticks<=ticks+1;
  if(!reset_n) begin divider<=0;enable_run<=1;end
  else begin divider<=divider+1;if(divider==15)enable_run<=!STRESS || ticks%257<180;end
 end
 wire ce=divider==0 && enable_run,cf=divider==8 && enable_run;
 wire wait_n=!STRESS || ticks%113<70;
 wire [23:0] a;wire mr,io,rf,rd,wr,m1,halt_n;wire [7:0] dout;
 wire int_n=!(GUARD>=0 && cpu.u0.adl_mode);
 wire nmi_n=!(GUARD==7 && cpu.u0.adl_mode && cpu.u0.pc>=24'h010001);
 reg [7:0] rom[0:65535];integer i;
 function automatic [7:0] data_at(input [23:0] adr);
  if(adr[23:16]==0)data_at=rom[adr[15:0]];
  else if(GUARD>=0 && adr==24'h010000)data_at=8'hfb;
  else if(GUARD>=0 && adr==24'h010001)data_at=0;
  else if(GUARD>=0 && adr==24'h010002)begin
   if(GUARD>=8)begin
    // R18: canonical SIL/LIL RSTs now use frames. Keep no-write tests
    // as different-vector noncanonical SIS/LIS guards instead.
    if(GUARD==16)data_at=8'h40;else if(GUARD==19)data_at=8'h49;else
    case((GUARD-8)/3) 0:data_at=8'h40;1:data_at=8'h49;2:data_at=8'h52;3:data_at=8'h5b;endcase
   end else case(GUARD)
   0:data_at=8'hcd;1:data_at=8'hc9;2:data_at=8'hc7;3:data_at=8'hc2;
   4:data_at=8'h18;5:data_at=8'hdd;6,7:data_at=8'hed;
   default:data_at=0;endcase
  end else if(GUARD>=0 && adr==24'h010003)begin
   if(GUARD>=8)begin
    if(GUARD==16)data_at=8'hcf;else if(GUARD==19)data_at=8'hd7;else
    case((GUARD-8)%3)0:data_at=8'hcd;1:data_at=8'hc9;2:data_at=8'hc7;endcase
   end else case(GUARD)5:data_at=8'he9;6:data_at=8'h4d;7:data_at=8'h45;default:data_at=0;endcase
  end else data_at=0;
 endfunction
 wire [7:0] din=(!mr && !rd)?data_at(a):8'hff;
 G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(clk),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(int_n),.NMI_n(nmi_n),.BUSRQ_n(1'b1),.DI(din),.A24(a),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
 integer sequence_index=0,waits=0,pauses=0;reg seen_target=0,hold_valid=0;
 reg [63:0] held,now_state;
 always @(posedge clk) if(reset_n)begin
  if(!mr && !wr)$fatal(1,"unexpected memory write in PC/control fixture");
  if(!io && !m1)$fatal(1,"IRQ acknowledged in ADL guard fixture");
  if(!enable_run)pauses=pauses+1;
  if(ce)begin
   now_state={a,cpu.u0.pc,cpu.u0.adl_mode,cpu.u0.sp[14:0]};
   if(cpu.u0.tstate==2 && !cpu.u0.wait_n)begin
    if(hold_valid && now_state!==held)$fatal(1,"PC/address changed during WAIT");
    held=now_state;hold_valid=1;waits=waits+1;
   end else hold_valid=0;
   if(cpu.u0.mcycle==1 && cpu.u0.tstate==2 && cpu.u0.wait_n && GUARD<0)begin
    if(!seen_target && a==(TARGET_ADL?24'hfffffe:24'h00fffe))seen_target=1;
    if(seen_target)begin
     case(sequence_index)
     0:if(a!==(TARGET_ADL?24'hfffffe:24'h00fffe))$fatal(1,"wrong first fetch");
     1:if(a!==(TARGET_ADL?24'hffffff:24'h00ffff))$fatal(1,"wrong boundary fetch");
     2:begin
      if(a!==0 || cpu.u0.pc!==0 || cpu.u0.adl_mode!==TARGET_ADL)$fatal(1,"PC wrap/mode error a=%h PC=%h ADL=%d",a,cpu.u0.pc,cpu.u0.adl_mode);
      if(STRESS && (waits==0 || pauses==0))$fatal(1,"missing stress coverage");
      $display("PASS pc_r9 ADL=%0d stress=%0d WAIT=%0d pauses=%0d",TARGET_ADL,STRESS,waits,pauses);$finish;
     end
     endcase
     sequence_index=sequence_index+1;
    end
   end
  end
 end
 always @(negedge clk) if(reset_n)begin
  if(!rf && a[23:16]!=0)$fatal(1,"refresh retained bank");
  if(!halt_n)begin
   if(GUARD<0 || cpu.u0.adl_mode!==1 || cpu.u0.sp!==16'hf000 || cpu.u0.spl!==24'hffffff || cpu.u0.inte_ff1!==1 || cpu.u0.intcycle || cpu.u0.nmicycle)$fatal(1,"unsupported control failed closed sp=%h spl=%h iff=%d",cpu.u0.sp,cpu.u0.spl,cpu.u0.inte_ff1);
   $display("PASS mixed_guard_r10 kind=%0d no SPS/SPL write, no ADL IRQ/NMI entry",GUARD);$finish;
  end
 end
 initial begin
  for(i=0;i<65536;i=i+1)rom[i]=0;
  rom[0]=8'hc3;rom[1]=0;rom[2]=1;
  {rom[16'h100],rom[16'h101],rom[16'h102],rom[16'h103],rom[16'h104],rom[16'h105],rom[16'h106],rom[16'h107],rom[16'h108],rom[16'h109],rom[16'h10a],rom[16'h10b],rom[16'h10c],rom[16'h10d],rom[16'h10e]}=
   {8'hf3,8'h31,8'h00,8'hf0,8'h01,8'he7,8'he7,8'h3e,8'ha5,8'hed,8'h79,8'h3e,8'h5a,8'hed,8'h79};
  rom[16'h10f]=TARGET_ADL||GUARD>=0?8'h5b:8'h40;rom[16'h110]=8'hc3;
  rom[16'h111]=GUARD>=0?0:8'hfe;rom[16'h112]=GUARD>=0?0:8'hff;
  if(TARGET_ADL || GUARD>=0)rom[16'h113]=GUARD>=0?1:8'hff;
  repeat(12)@(negedge clk);reset_n=1;
 end
 initial begin #20000000;$fatal(1,"PC fixture timeout pc=%h a=%h",cpu.u0.pc,a);end
endmodule
