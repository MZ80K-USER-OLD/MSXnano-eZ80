`timescale 1ns/1ps
`include "EZ80M7.vh"
// Run the actual COM bytes, including its loader and DOS return.
// BDOS function 9 is a tiny Z80 routine that emits characters to port F0h.
module tb_mul_corners_r7;
    parameter INTERNAL_WAIT=0, FETCH_WAIT=0, PAUSE_ENABLE=0, PHASE=0, FAULT=0, EXTENDED=1, CPU_DIV=16, LOGTEST=0, RUN_REQUEST=1;
    reg c108=0,c54=0,c27=0,reset_n=0;
    always #5 c108=~c108;
    always #10 c54=~c54;
    always #20 c27=~c27;
    reg [1:0] dot=0;
    reg dh=0,dl=0;
    always @(posedge c27) begin
        if(!reset_n) begin dot<=0;dh<=0;dl<=0;end
        else begin
            dot<={dot[0],!dot[1]};
            case(dot)
                0: begin dh<=0;dl<=1;end
                1: begin dh<=1;dl<=0;end
                3: begin dh<=0;dl<=0;end
                2: begin dh<=1;dl<=1;end
            endcase
        end
    end
    reg [3:0] divider=0;
    always @(posedge c54) if(!reset_n) divider<=PHASE%CPU_DIV;
                        else if(divider==CPU_DIV-1) divider<=0;else divider<=divider+1;
    reg [31:0] ticks=0;
    always @(posedge c54) if(!reset_n) ticks<=0;else ticks<=ticks+1;
    // Pause complete CPU T-state periods: rising and falling enables stay paired.
    // Do not suppress only one half of an external bus cycle.
    reg enable_run=1;
    always @(posedge c54) begin
        if(!reset_n) enable_run<=1;
        else if(divider==CPU_DIV-1) enable_run<=!PAUSE_ENABLE || ticks%257<180;
    end
    wire fetch_wait_n=!FETCH_WAIT || ticks%131<97;
    wire internal_wait_n=!INTERNAL_WAIT || !cpu.u0.mul_active || cpu.u0.tstate<4;
    wire [23:0] a;
    wire mr,io,rf,rd,wr,m1,halt_n;
    wire [7:0] dout;
    reg [7:0] din;
    wire mm,ext,wait_n,req,rw,done;
    wire [15:0] ma;
    wire [22:0] ra;
    wire [7:0] ext_di,wd,ramdata;
    // Hold INT active during high-address cycles. All such work must be DI.
    reg int_n=1;
    G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(c54),.clk_enable(divider==0 && enable_run),.clk_falling(divider==CPU_DIV/2 && enable_run),
        .WAIT_n(wait_n && fetch_wait_n && internal_wait_n),.INT_n(int_n),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),
        .A24(a),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
    ez80_memory_bridge bridge(c54,reset_n,a,mr,io,rf,rd,wr,dout,
        mm,ma,ext,wait_n,ext_di,req,rw,ra,wd,done,ramdata);
    wire [22:0] fault_address = ra;
    wire [7:0] fault_data = FAULT==1 && ra==23'h6a0102 ? wd^8'h01 : wd;
    wire cs,ras,cas,we,sc,cke;
    wire [31:0] dq;
    wire [10:0] sa;
    wire [1:0] ba;
    wire [3:0] dm;
    memory_ctrl_ez80 mem(
        .clk_27m(c54),.clk_108m(c108),.bus_reset_n(reset_n),.video_dhclk(dh),.video_dlclk(dl),
        .mapper_din(8'h00),.mapper_req(1'b0),.mapper_write(1'b0),.mapper_addr(22'h0),
        .megaram_req(1'b0),.megaram_write(1'b0),.megaram_addr(21'h0),
        .vram_addr(17'h0),.vram_write(1'b0),.vram_din(8'h0),.bus_rfsh_n(rf),
        .ext_req(req),.ext_write(rw),.ext_addr(fault_address),.ext_din(fault_data),.ext_done(done),.ext_dout(ramdata),
        .O_sdram_clk(sc),.O_sdram_cke(cke),.O_sdram_cs_n(cs),.O_sdram_ras_n(ras),
        .O_sdram_cas_n(cas),.O_sdram_wen_n(we),.IO_sdram_dq(dq),
        .O_sdram_addr(sa),.O_sdram_ba(ba),.O_sdram_dqm(dm));
    sdram_model33 ram(sc,{cs,ras,cas,we},sa,ba,dm,dq);
    reg [7:0] lowmem[0:65535];
    integer i,j=0,waits=0,high_fetches=0,bank_writes=0,bdos_calls=0;
    reg io_write_old=0,bdos_old=0,seen_adl=0,seen_return=0;
    string output_text="";
    reg [7:0] expected_status;
    reg [23:0] trace_previous=24'hffffff;
    integer trace_count=0;
    reg [7:0] trace_stage=0;
    always @(posedge c54) begin
        if(reset_n && !mm && !wr && ma==`M7_FAIL_STAGE && dout!=trace_stage) begin
            trace_stage=dout;$display("COM stage %c time=%0t",dout,$time);$fflush;
        end
        din<=ext?ext_di:(!mm && !rd?lowmem[ma]:8'hff);
        if(reset_n && !mm && !wr) lowmem[ma]<=dout;

        if(reset_n && !wait_n) waits=waits+1;
        if(reset_n && !m1 && !mr && rf && a[23:16]!=0) $fatal(1,"R3 instruction fetch escaped bank00");
        if(reset_n && ext && !mm) $fatal(1,"high memory reached MSX decode");


        if(reset_n && req && rw) begin
            if(ra>=23'h400000 && ra<23'h640000) $fatal(1,"COM touched MegaRAM/VRAM a=%h physical=%h pc=%h mc=%h ir=%h bank=%h",a,ra,cpu.u0.pc,cpu.u0.mcycle,cpu.u0.ir,cpu.u0.a_bank);
            bank_writes=bank_writes+1;
        end
        if(reset_n && !m1 && !mr && a==5 && !bdos_old) begin
            bdos_calls=bdos_calls+1;
            if(cpu.u0.inte_ff1!==1)
                $fatal(1,"BDOS call outside Z80/MBASE0/EI");
            if(EXTENDED && cpu.u0.extensions_enabled!==0) $fatal(1,"extensions not locked for DOS");
        end
        bdos_old<=!m1 && !mr && a==5;
        if(reset_n && !io && !wr && a[7:0]==8'hf0 && !io_write_old) begin
            output_text={output_text,dout};$write("%c",dout);
        end
        io_write_old<=!io && !wr && a[7:0]==8'hf0;
        if(reset_n && !m1 && !mr && a==24'h000080) begin
            expected_status=!EXTENDED?3:(FAULT?2:1);
            if(lowmem[`M7_STATUS]!==expected_status) $fatal(1,"wrong COM status %h expected %h",lowmem[`M7_STATUS],expected_status);
            if(cpu.u0.sp!==16'hf000 || cpu.u0.inte_ff1!==1)
                $fatal(1,"DOS return state not restored");
            if(EXTENDED && cpu.u0.extensions_enabled!==0) $fatal(1,"extensions not locked on return");
            if({lowmem[16'ha1],lowmem[16'ha0]}!==16'h1357 || {lowmem[16'ha3],lowmem[16'ha2]}!==16'h2468)
                $fatal(1,"caller IX/IY not restored");
            if(lowmem[16'hffff]!==8'h5c || lowmem[`M7_GUARD]!==8'ha6) $fatal(1,"MSX guard/slot changed");
            if(bdos_calls!=1) $fatal(1,"wrong DOS print call count %d",bdos_calls);
            if(FETCH_WAIT && wait_samples==0) $fatal(1,"missing ADL execution/return/WAIT");
            if(!EXTENDED && bank_writes!=0) $fatal(1,"unsupported profile touched high memory");
            if(captures!=71 || products!=71 || commits!=71 || irq_count!=1 || !isr_seen || (INTERNAL_WAIT && internal_wait_samples==0) || (PAUSE_ENABLE && paused_samples==0))
                $fatal(1,"coverage capture=%d products=%d commits=%d IRQ=%d handler=%d internalWAIT=%d pause=%d",captures,products,commits,irq_count,isr_seen,internal_wait_samples,paused_samples);
            $display("COVERAGE MLT=%0d IRQ=%0d internal_WAIT=%0d paused=%0d",commits,irq_count,internal_wait_samples,paused_samples);
            $display("PASS mul_corners_r7 phase=%0d fault=%0d extended=%0d cpu_div=%0d status=%0d high_fetch_ticks=%0d WAIT_ticks=%0d",PHASE,FAULT,EXTENDED,CPU_DIV,expected_status,high_fetches,waits);
            $finish;
        end
    end
    integer captures=0,products=0,commits=0,irq_count=0,wait_samples=0,internal_wait_samples=0,paused_samples=0;
    reg triggered=0,ack_seen=0,isr_seen=0,previous_intcycle=0,last_commit=0,pause_valid=0;
    reg [335:0] pause_snapshot,current_snapshot;
    reg [127:0] packed_regs;
    integer k;
    always @(posedge c54) if(reset_n) begin
        if(divider==0 && enable_run) begin
            last_commit=cpu.u0.mul_commit;
            if(!fetch_wait_n) wait_samples=wait_samples+1;
            if(cpu.u0.mul_active && cpu.u0.mcycle==1) begin
                if(cpu.u0.tstate==4) captures=captures+1;
                if(cpu.u0.tstate==5) products=products+1;
                if(cpu.u0.mul_commit) commits=commits+1;
                if(!internal_wait_n && !cpu.u0.wait_n) internal_wait_samples=internal_wait_samples+1;
                if(cpu.u0.tstate>=4 && (!mr || !io)) $fatal(1,"MLT emitted external data cycle");
            end
        end
        for(k=0;k<8;k=k+1) packed_regs[k*16+:16]={cpu.u0.regs.regsh[k],cpu.u0.regs.regsl[k]};
        current_snapshot={packed_regs,cpu.u0.mul_left,cpu.u0.mul_right,cpu.u0.mul_product,cpu.u0.upper,cpu.u0.f,cpu.u0.sp,cpu.u0.spl,cpu.u0.pc};
        if(!enable_run) begin
            if(pause_valid && current_snapshot!==pause_snapshot) $fatal(1,"MLT/register changed while CEN disabled");
            pause_snapshot=current_snapshot;pause_valid=1;paused_samples=paused_samples+1;
        end else pause_valid=0;
    end
    always @(negedge c54) if(reset_n) begin
        if(lowmem[16'hb2]==1 && cpu.u0.mul_active && cpu.u0.tstate==5 && !triggered) begin int_n=0;triggered=1;end
        if(!io && !m1 && !ack_seen) begin
            if(!triggered || lowmem[16'hb2]!=1) $fatal(1,"unexpected IRQ acknowledgement");
            int_n=1;ack_seen=1;irq_count=irq_count+1;
        end
        if(cpu.u0.intcycle && !previous_intcycle) begin
            if(!last_commit || commits!=71) $fatal(1,"IRQ accepted before MLT commit");
        end
        previous_intcycle=cpu.u0.intcycle;
        if(!m1 && !mr && rf && a==24'h38 && !isr_seen) begin
            if(!ack_seen || cpu.u0.sp!==16'heff8 || {lowmem[16'heff9],lowmem[16'heff8]}!==`M7_IRQ_AFTER)
                $fatal(1,"MLT IRQ stack/restart PC");
            isr_seen=1;
        end
    end
    initial begin
        for(i=0;i<65536;i=i+1) lowmem[i]=0;
        // Simulation-only IM1 vector. This never patches an MSX hardware BIOS.
        {lowmem[16'h38],lowmem[16'h39],lowmem[16'h3a]}={8'hc3,8'hc0,8'h00};
        {lowmem[16'hc0],lowmem[16'hc1],lowmem[16'hc2],lowmem[16'hc3],lowmem[16'hc4],lowmem[16'hc5],lowmem[16'hc6],lowmem[16'hc7],lowmem[16'hc8],lowmem[16'hc9],lowmem[16'hca],lowmem[16'hcb],lowmem[16'hcc],lowmem[16'hcd],lowmem[16'hce],lowmem[16'hcf]}=
          {8'hf5,8'hc5,8'hd5,8'he5,8'h3a,8'hb0,8'h00,8'h3c,8'h32,8'hb0,8'h00,8'he1,8'hd1,8'hc1,8'hf1,8'hfb};
        lowmem[16'hd0]=8'hed;lowmem[16'hd1]=8'h4d;
        // Reset stub, a tiny BDOS-9 routine, and a DOS-style caller.
        lowmem[0]=8'hc3;lowmem[1]=8'h40;lowmem[2]=0;
        {lowmem[5],lowmem[6],lowmem[7]}={8'hc3,8'h10,8'h00};
        // Deliberately enable interrupts INSIDE the system-call stub.
        // Its caller may not rely on DI surviving an MSX-DOS/BIOS call.
        lowmem[16'h10]=8'hfb;lowmem[16'h11]=8'h00;
        {lowmem[16'h12],lowmem[16'h13],lowmem[16'h14],lowmem[16'h15],lowmem[16'h16],
         lowmem[16'h17],lowmem[16'h18],lowmem[16'h19],lowmem[16'h1a],lowmem[16'h1b]}=
            {8'h1a,8'hfe,8'h24,8'hc8,8'hd3,8'hf0,8'h13,8'hc3,8'h10,8'h00};
        // EI; NOP; SP=F000; IX=1357; IY=2468; CALL 0100;
        {lowmem[16'h40],lowmem[16'h41],lowmem[16'h42],lowmem[16'h43],lowmem[16'h44],
         lowmem[16'h45],lowmem[16'h46],lowmem[16'h47],lowmem[16'h48],lowmem[16'h49],lowmem[16'h4a],lowmem[16'h4b],lowmem[16'h4c],
         lowmem[16'h4d],lowmem[16'h4e],lowmem[16'h4f]}=
            {8'hfb,8'h00,8'h31,8'h00,8'hf0,8'hdd,8'h21,8'h57,8'h13,8'hfd,8'h21,8'h68,8'h24,8'hcd,8'h00,8'h01};
        // Snapshot returned IX/IY then JP 0080h.
        {lowmem[16'h50],lowmem[16'h51],lowmem[16'h52],lowmem[16'h53],lowmem[16'h54],lowmem[16'h55],
         lowmem[16'h56],lowmem[16'h57],lowmem[16'h58],lowmem[16'h59],lowmem[16'h5a],lowmem[16'h5b],
         lowmem[16'h5c],lowmem[16'h5d],lowmem[16'h5e]}=
            {8'hdd,8'he5,8'he1,8'h22,8'ha0,8'h00,8'hfd,8'he5,8'he1,8'h22,8'ha2,8'h00,8'hc3,8'h80,8'h00};
        lowmem[16'h80]=8'h76;lowmem[16'hffff]=8'h5c;
        $readmemh("sim/mul_corners/EZ80M7.hex",lowmem,16'h100,`M7_COM_END);
        lowmem[16'h80]=0;
        if(RUN_REQUEST!=0) begin
            lowmem[16'h80]=5;lowmem[16'h81]=" ";lowmem[16'h82]="/";lowmem[16'h83]="R";lowmem[16'h84]="U";lowmem[16'h85]=RUN_REQUEST==1?"N":"X";
        end
        repeat(12) @(negedge c54);reset_n=1;
        @(negedge c108);mem.RstSeq=24;
    end
    initial begin #400000000;$fatal(1,"COM timeout a=%h stage=%c status=%h",a,lowmem[`M7_FAIL_STAGE],lowmem[`M7_STATUS]);end
    initial if($test$plusargs("TRACE")) begin #1000000;$display("TRACE END a=%h stage=%c status=%h",a,lowmem[`M7_FAIL_STAGE],lowmem[`M7_STATUS]);$finish;end
endmodule
