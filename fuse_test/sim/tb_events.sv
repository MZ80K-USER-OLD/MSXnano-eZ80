`timescale 1ns/1ps
module tb_fuse;
 reg clk=0,rst=0,active=0,run_enable=0,int_pin=1,nmi_pin=1;integer div=1;
 wire ce=run_enable&&(div==0),cf=run_enable&&(div==2);
 wire [23:0]adr;wire[7:0]dout;reg[7:0]din;wire mr,io,rd,wr,rf,m1,hn;
 reg [7:0]mem[0:16777215];integer touched[0:65535];integer nt=0;
 reg [23:0]st[0:21];integer in_fd,out_fd,rc,idx,steps,seed,nmem,code_len,ma,mv,k,t,completed,status,seen_fetch,done;
 integer repeat_instruction=0;integer evs[0:2];integer ev,j;reg fake_boundary,in_interrupt,normal_retire,interrupt_retire,snapshot_ready;
 wire [23:0]request_adr=cpu.request_address;
 integer max_cycles=4096;reg prev_boundary;string infile,outfile;
 G80A_eZ80 cpu(.CLK_n(clk),.RESET_n(rst),.clk_enable(ce),.clk_falling(cf),.WAIT_n(1'b1),.INT_n(int_pin),.NMI_n(nmi_pin),.BUSRQ_n(1'b1),.DI(din),.Trace_Data(8'h00),.A24(adr),.DO(dout),.MREQ_n(mr),.IORQ_n(io),.RD_n(rd),.WR_n(wr),.RFSH_n(rf),.M1_n(m1),.HALT_n(hn));
 function [7:0]peek(input[23:0]a);begin peek=(^mem[a]===1'bx)?8'h00:mem[a];end endfunction
 always @* begin
  if(!cpu.intcycle_n && cpu.mcycle==1)din=seed;
  else if(cpu.request_io)din=(request_adr[15:0]^(request_adr[15:0]>>8)^seed)&255;
  else din=peek(request_adr);
 end
 function [23:0]pair(input integer n);begin pair={cpu.u0.regs.regsu[63-n*8-:8],cpu.u0.regs.regsh[n],cpu.u0.regs.regsl[n]};end endfunction
 task tick;begin #5;clk=1;#5;clk=0;#1;div=(div+1)%4;#0.01;end endtask
 always @(negedge clk)if(active && cf && cpu.tstate==3 && cpu.busak_n_i && !cpu.noread && !(!cpu.intcycle_n && cpu.mcycle==1))begin
  if(cpu.request_io)begin
   if(cpu.request_write)$fwrite(out_fd,"EV PW %h %h\n",request_adr[15:0],dout);
   else $fwrite(out_fd,"EV PR %h %h\n",request_adr[15:0],din);
  end else if(cpu.request_write)begin
   mem[request_adr]=dout;touched[nt]=request_adr;nt=nt+1;
   $fwrite(out_fd,"EV MW %h %h\n",request_adr,dout);
  end else $fwrite(out_fd,"EV %s %h %h\n",cpu.mcycle==1?"IF":"MR",request_adr,din);
 end
 function [23:0]state_value(input integer n);begin
 case(n)
 0:state_value={cpu.u0.acc,cpu.u0.f};
 1:state_value=pair(cpu.u0.alternate?4:0);
 2:state_value=pair(cpu.u0.alternate?5:1);
 3:state_value=pair(cpu.u0.alternate?6:2);
 4:state_value={cpu.u0.ap,cpu.u0.fp};
 5:state_value=pair(cpu.u0.alternate?0:4);
 6:state_value=pair(cpu.u0.alternate?1:5);
 7:state_value=pair(cpu.u0.alternate?2:6);
 8:state_value=pair(3);9:state_value=pair(7);
 10:state_value=cpu.u0.spl;11:state_value=cpu.u0.pc;
 12:state_value={cpu.u0.i_upper,cpu.u0.i};13:state_value=cpu.u0.r;
 14:state_value=cpu.u0.inte_ff1;15:state_value=cpu.u0.inte_ff2;
 16:state_value=cpu.u0.istatus;17:state_value=cpu.u0.halt_ff;
 18:state_value=cpu.u0.adl_mode;19:state_value=cpu.u0.mbase;
 20:state_value=cpu.u0.madl;21:state_value=cpu.u0.sp;
 default:state_value=24'hxxxxxx;
 endcase
 end endfunction
 // Pending NMI represents one sampled pulse; its external pin is high again.
 task inject(input integer event_value);begin
 ev=event_value;
 `include "event_inject.vh"
 #0.01;end endtask
 task snapshot;integer a;begin
  $fwrite(out_fd,"STATE");for(a=0;a<22;a=a+1)$fwrite(out_fd," %h",state_value(a));$fwrite(out_fd,"\n");
  for(a=0;a<nt;a=a+1)$fwrite(out_fd,"MEM %h %h\n",touched[a],mem[touched[a]]);
  $fwrite(out_fd,"END %0d %0d\n",status,t);
 end endtask
 initial begin
  if(!$value$plusargs("INPUT=%s",infile)||!$value$plusargs("OUTPUT=%s",outfile))$fatal(1,"INPUT and OUTPUT required");
  rc=$value$plusargs("MAX_CYCLES=%d",max_cycles);
  in_fd=$fopen(infile,"r");out_fd=$fopen(outfile,"w");if(!in_fd||!out_fd)$fatal(1,"file open failed");
  while(!$feof(in_fd))begin
   rc=$fscanf(in_fd,"%h %h %h %h %h %h",idx,steps,seed,nmem,code_len,repeat_instruction);
   if(rc==6)begin
    for(j=0;j<3;j=j+1)begin rc=$fscanf(in_fd,"%h",evs[j]);if(rc!=1)$fatal(1,"event input truncated");end
    active=0;int_pin=1;nmi_pin=1;run_enable=0;rst=0;div=1;tick;tick;tick;tick;
    for(k=0;k<nt;k=k+1)mem[touched[k]]=0;nt=0;
    for(k=0;k<22;k=k+1)begin rc=$fscanf(in_fd,"%h",st[k]);if(rc!=1)$fatal(1,"state input truncated");end
    for(k=0;k<nmem;k=k+1)begin rc=$fscanf(in_fd,"%h %h",ma,mv);if(rc!=2)$fatal(1,"memory input truncated");mem[ma]=mv;touched[nt]=ma;nt=nt+1;end
    rst=1;run_enable=1;div=0;tick;run_enable=0;repeat(8)tick;div=1;#1;
    if(cpu.reset_s!==1'b1)$fatal(1,"reset synchronizer not released");
    `include "init_state.vh"
    #1;
    for(k=0;k<22;k=k+1)if(state_value(k)!==st[k])$fatal(1,"initial state roundtrip failed case=%d field=%d exp=%h act=%h",idx,k,st[k],state_value(k));
    fake_boundary=(evs[0]!=0);in_interrupt=0;snapshot_ready=0;
    if(fake_boundary)begin
     `include "event_start.vh"
     inject(evs[0]);
    end
    run_enable=1;$fwrite(out_fd,"BEGIN %0d\n",idx);active=1;status=1;completed=0;seen_fetch=0;done=0;
    for(t=0;t<max_cycles && !done;t=t+1)begin
     normal_retire=0;interrupt_retire=0;prev_boundary=0;
     if(snapshot_ready && ce && cpu.mcycle==1 && cpu.tstate==1)prev_boundary=1;
     if(ce && cpu.u0.frame_state==0 && !cpu.u0.intcycle && !cpu.u0.nmicycle && cpu.u0.mcycle==1 && cpu.u0.tstate==4)begin
      if(fake_boundary)fake_boundary=0;
      else begin
       normal_retire=1;
       if(completed+1<3 && evs[completed+1]!=0)inject(evs[completed+1]);
      end
     end
     tick;
     if(normal_retire)completed=completed+1;
     if(cpu.u0.intcycle || cpu.u0.nmicycle || cpu.u0.frame_state!=0)in_interrupt=1;
     else if(in_interrupt && cpu.mcycle==1 && cpu.tstate==1)begin
      in_interrupt=0;completed=completed+1;interrupt_retire=1;
     end
     if(completed>=steps)snapshot_ready=1;
     if(prev_boundary)begin done=1;status=0;end
     if(cpu.u0.frame_state==7)begin done=1;status=2;end
    end
    active=0;snapshot;
    if(idx%1000==0)$display("PROGRESS idx=%0d status=%0d cycles=%0d",idx,status,t);
   end
  end
  $fclose(in_fd);$fclose(out_fd);$display("DONE");$finish;
 end
endmodule
