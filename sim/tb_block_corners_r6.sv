`timescale 1ns/1ps
`include "EZ80B6.vh"
// Run the actual COM bytes, including its loader and DOS return.
// BDOS function 9 is a tiny Z80 routine that emits characters to port F0h.
module tb_block_corners_r6;
    parameter NEGATIVE=0, WAIT_PROFILE=0, PAUSE_ENABLE=0, PHASE=0, FAULT=0, EXTENDED=1, CPU_DIV=16, LOGTEST=0, RUN_REQUEST=1;
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
    integer ticks=0;
    reg enable_run=1;
    always @(posedge c54) begin
        ticks<=ticks+1;
        if(!reset_n) enable_run<=1;
        else if(divider==CPU_DIV-1) enable_run<=!PAUSE_ENABLE || ticks%257<180;
    end
    wire ce=divider==0 && enable_run;
    wire cf=divider==CPU_DIV/2 && enable_run;
    reg forced_wait_n=1;
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
    G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(c54),.clk_enable(ce),.clk_falling(cf),
        .WAIT_n(wait_n && forced_wait_n),.INT_n(int_n),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),
        .A24(a),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
    ez80_memory_bridge bridge(c54,reset_n,a,mr,io,rf,rd,wr,dout,
        mm,ma,ext,wait_n,ext_di,req,rw,ra,wd,done,ramdata);
    wire [22:0] fault_address = ra;
    wire [7:0] fault_data = FAULT==1 && ra==23'h6cffff ? wd^8'h01 : wd;
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
        if(reset_n && !mm && !wr && ma==`B6_FAIL_STAGE && dout!=trace_stage) begin
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
            if(lowmem[`B6_STATUS]!==expected_status) $fatal(1,"wrong COM status %h expected %h",lowmem[`B6_STATUS],expected_status);
            if(cpu.u0.sp!==16'hf000 || cpu.u0.inte_ff1!==1)
                $fatal(1,"DOS return state not restored");
            if(EXTENDED && cpu.u0.extensions_enabled!==0) $fatal(1,"extensions not locked on return");
            if({lowmem[16'ha1],lowmem[16'ha0]}!==16'h1357 || {lowmem[16'ha3],lowmem[16'ha2]}!==16'h2468)
                $fatal(1,"caller IX/IY not restored");
            if(lowmem[16'hffff]!==8'h5c || lowmem[`B6_GUARD]!==8'ha6) $fatal(1,"MSX guard/slot changed");
            if(bdos_calls!=1) $fatal(1,"wrong DOS print call count %d",bdos_calls);
            if(EXTENDED && waits==0) $fatal(1,"missing ADL execution/return/WAIT");
            if(!EXTENDED && bank_writes!=0) $fatal(1,"unsupported profile touched high memory");
            if(irq_total!=9 || seen_case!=15 || wait_samples==0 || wait_read==0 || wait_write==0 || wait_internal==0)
                $fatal(1,"coverage irq=%d cases=%d wait=%d read=%d write=%d",irq_total,seen_case,wait_samples,wait_read,wait_write);
            $display("COVERAGE cases=%0d IRQ=%0d read_WAIT=%0d write_WAIT=%0d internal_WAIT=%0d",seen_case,irq_total,wait_read,wait_write,wait_internal);
            $display("PASS block_corners_r6 phase=%0d fault=%0d extended=%0d cpu_div=%0d status=%0d high_fetch_ticks=%0d WAIT_ticks=%0d",PHASE,FAULT,EXTENDED,CPU_DIV,expected_status,high_fetches,waits);
            $finish;
        end
    end
    wire block_active=cpu.u0.iset==2 && cpu.u0.ir[7:5]==3'b101 && cpu.u0.ir[2:1]==0 && !cpu.u0.intcycle && !cpu.u0.nmicycle;
    integer active_case=-1, seen_case=0, iterations=0, irq_total=0;
    integer trigger_kind[0:14],irq_expected[0:14],steps_expected[0:14],irq_step[0:14],restart_expected[0:14];
    reg [15:0] block_pc[0:14],after_pc[0:14];
    reg triggered=0,ack_seen=0,isr_seen=0,wait_started=0;
    integer wait_left=0, wait_samples=0, wait_read=0,wait_write=0,wait_internal=0;
    reg previous_intcycle=0;
    reg [2:0] last_mc=0;
    reg last_res=0,last_wait=1;
    reg [335:0] held, now_state;
    reg [127:0] packed_regs;
    integer k;
    reg hold_valid=0;
    // All stimuli are synchronous to the board clock; a T1 wait request reaches
    // the wrapper's falling-edge sample before the core tests WAIT at T2.
    always @(negedge c54) begin
        if(reset_n) begin
            if(lowmem[16'hb2]!=1) begin
                if(active_case>=0 && (iterations!=steps_expected[active_case] || ack_seen!=irq_expected[active_case] || isr_seen!=irq_expected[active_case]))
                    $fatal(1,"case completion count case=%d steps=%d ack=%d handler=%d",active_case,iterations,ack_seen,isr_seen);
                int_n=1;triggered=0;ack_seen=0;isr_seen=0;active_case=-1;iterations=0;
            end else begin
                if(active_case<0) begin active_case=lowmem[16'hb1];seen_case=seen_case+1;end
                if(!triggered && ((trigger_kind[active_case]==3 && !m1 && !mr && rf && a==block_pc[active_case]) ||
                   (trigger_kind[active_case]!=3 && block_active && cpu.u0.tstate==2 && !cpu.u0.wait_n &&
                     ((trigger_kind[active_case]==2 && cpu.u0.mcycle==3) ||
                      ((trigger_kind[active_case]==1 || trigger_kind[active_case]==4) && cpu.u0.mcycle==2)) &&
                     (trigger_kind[active_case]!=4 || iterations==steps_expected[active_case])))) begin
                    int_n=0;triggered=1;
                end
                if(!io && !m1 && !ack_seen) begin
                    if(!irq_expected[active_case] || iterations!=irq_step[active_case]) $fatal(1,"IRQ count/boundary case=%d steps=%d",active_case,iterations);
                    ack_seen=1;int_n=1;irq_total=irq_total+1;
                end
                if(!m1 && !mr && rf && a==24'h38 && !isr_seen) begin
                    if(!ack_seen || cpu.u0.sp!==16'heff8) $fatal(1,"IRQ SPS case=%d sp=%h ack=%d irq_total=%d intcycle=%b",active_case,cpu.u0.sp,ack_seen,irq_total,cpu.u0.intcycle);
                    if({lowmem[16'heff9],lowmem[16'heff8]} !== (restart_expected[active_case]?block_pc[active_case]:after_pc[active_case]))
                        $fatal(1,"IRQ return PC case=%d saved=%h prefix=%h after=%h",active_case,{lowmem[16'heff9],lowmem[16'heff8]},block_pc[active_case],after_pc[active_case]);
                    isr_seen=1;
                end
            end
            if(cpu.u0.intcycle && !previous_intcycle) begin
                if(!last_res || (last_mc!=3 && last_mc!=4) || !last_wait)
                    $fatal(1,"IRQ accepted outside byte boundary mc=%d res=%d wait=%d",last_mc,last_res,last_wait);
            end
            if(cpu.u0.intcycle && !previous_intcycle) $display("IRQ entry case=%d steps=%d",active_case,iterations);
            previous_intcycle=cpu.u0.intcycle;
            if(wait_left>0) begin forced_wait_n=0;wait_left=wait_left-1;end
            else forced_wait_n=1;
            if(cpu.u0.tstate!=1) wait_started=0;
            if(!wait_started && block_active && cpu.u0.tstate==1 &&
               (cpu.u0.mcycle>=2 && cpu.u0.mcycle<=4)) begin
                wait_started=1;wait_left=(6+WAIT_PROFILE)*CPU_DIV;forced_wait_n=0;
            end
        end
    end
    always @(posedge c54) if(reset_n && ce) begin
        last_mc=cpu.u0.mcycle;last_res=cpu.u0.t_res;last_wait=cpu.u0.wait_n;
        if(block_active && cpu.u0.mcycle==1 && cpu.u0.tstate==3) iterations=iterations+1;
        for(k=0;k<8;k=k+1) packed_regs[k*16+:16]={cpu.u0.regs.regsh[k],cpu.u0.regs.regsl[k]};
        now_state={packed_regs,a,dout,cpu.u0.upper,cpu.u0.regbusa,cpu.u0.regbusb,cpu.u0.regbusc,cpu.u0.sp,cpu.u0.spl,cpu.u0.pc,cpu.u0.f};
        if(block_active && cpu.u0.tstate==2 && !cpu.u0.wait_n) begin
            if(hold_valid && now_state!==held) $fatal(1,"state changed during WAIT case=%d mc=%d",active_case,cpu.u0.mcycle);
            held=now_state;hold_valid=1;wait_samples=wait_samples+1;
            if(cpu.u0.mcycle==2) wait_read=wait_read+1;
            if(cpu.u0.mcycle==3 && !cpu.u0.ir[0]) wait_write=wait_write+1;
            if(cpu.u0.mcycle==4 || (cpu.u0.mcycle==3 && cpu.u0.ir[0])) wait_internal=wait_internal+1;
        end else hold_valid=0;
    end
    // Expected-failure controls prove the assertions detect both regressions.
    initial if(NEGATIVE==1) force cpu.u0.instruction_has_width=0;
    always @(cpu.u0.intcycle) if(NEGATIVE==2) begin
        if(cpu.u0.intcycle) force cpu.ireq_inhibit=1;else release cpu.ireq_inhibit;
    end
    initial begin
        `include "case_plan.vh"
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
        $readmemh("sim/block_corners/EZ80B6.hex",lowmem,16'h100,`B6_COM_END);
        lowmem[16'h80]=0;
        if(RUN_REQUEST!=0) begin
            lowmem[16'h80]=5;lowmem[16'h81]=" ";lowmem[16'h82]="/";lowmem[16'h83]="R";lowmem[16'h84]="U";lowmem[16'h85]=RUN_REQUEST==1?"N":"X";
        end
        repeat(12) @(negedge c54);reset_n=1;
        @(negedge c108);mem.RstSeq=24;
    end
    initial begin #400000000;$fatal(1,"COM timeout a=%h stage=%c status=%h",a,lowmem[`B6_FAIL_STAGE],lowmem[`B6_STATUS]);end
    initial if($test$plusargs("TRACE")) begin #1000000;$display("TRACE END a=%h stage=%c status=%h",a,lowmem[`B6_FAIL_STAGE],lowmem[`B6_STATUS]);$finish;end
endmodule
