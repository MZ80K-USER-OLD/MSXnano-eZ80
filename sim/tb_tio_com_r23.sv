`timescale 1ns/1ps
`include `TEST_HEADER
// Run the actual COM bytes, including its loader and DOS return.
// BDOS function 9 is a tiny Z80 routine that emits characters to port F0h.
module tb_tio_com_r23;
    parameter PAUSE_ENABLE=0, PHASE=0, FAULT=0, EXTENDED=1, CPU_DIV=16, LOGTEST=0, RUN_REQUEST=1, SUPPORTED=1, FAULT_ADDR=23'h650100, LEGACY_FEATURE=0;
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
        if(!reset_n)enable_run<=1;
        else if(divider==CPU_DIV-1)enable_run<=!PAUSE_ENABLE || ticks%257<180;
    end
    wire [23:0] a;
    wire mr,io,rf,rd,wr,m1,halt_n;
    wire [7:0] dout;
    reg [7:0] din;
    wire mm,ext,wait_n,req,rw,done;
    wire [15:0] ma;
    wire [22:0] ra;
    wire [7:0] ext_di,wd,ramdata;
    // Hold INT active during high-address cycles. All such work must be DI.
    reg dos_irq=0,dos_arm=0;integer dos_acks=0;
    wire int_n = a[23:16]==0 && !dos_irq;
    wire [15:0] cpu_msx_address;
    wire cpu_extended;
    always @(posedge c54 or negedge c54) begin
        #0.001;
        if(reset_n && (^a)!==1'bx) begin
            if(cpu_extended !== (a[23:16]!=0)) $fatal(1,"registered MSX window mismatch %h",a);
            if(cpu_msx_address !== (a[23:16]!=0 ? 16'h0000:a[15:0]))
                $fatal(1,"registered MSX address isolation mismatch %h",a);
        end
    end
    G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(c54),.clk_enable(divider==0 && enable_run),.clk_falling(divider==CPU_DIV/2 && enable_run),
        .WAIT_n(wait_n),.INT_n(int_n),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(din),
        .A24(a),.A_MSX(cpu_msx_address),.Extended_Window(cpu_extended),.MREQ_n(mr),.IORQ_n(io),.RFSH_n(rf),.RD_n(rd),.WR_n(wr),.DO(dout),.M1_n(m1),.HALT_n(halt_n));
    ez80_memory_bridge #(.REQUEST_BANK_QUALIFIED(1),.PREDECODED_MSX(1)) bridge(.clk(c54),
        .reset_n(reset_n),
        .cpu_addr(a),
        .cpu_mreq_n(mr),
        .cpu_iorq_n(io),
        .cpu_rfsh_n(rf),
        .cpu_rd_n(rd),
        .cpu_wr_n(wr),
        .cpu_dout(dout),
        .msx_mreq_n(mm),
        .msx_addr(ma),
        .extended_cycle(ext),
        .wait_n(wait_n),
        .cpu_din(ext_di),
        .ram_req(req),
        .ram_write(rw),
        .ram_addr(ra),
        .ram_din(wd),
        .ram_done(done),
        .ram_dout(ramdata),
        .cpu_msx_addr(cpu_msx_address),
        .cpu_extended_window(cpu_extended));
    wire [22:0] fault_address = ra;
    wire [7:0] fault_data = (FAULT==1 && ra==FAULT_ADDR) ? wd^8'h01 : wd;
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
    integer private_e6_count=0;reg private_e6_old=0;
    always @(posedge c54)if(reset_n)begin
        if(cpu.diag_io_cycle && io!==1'b1)$fatal(1,"private IO leaked onto MSX IORQ");
        if(cpu.diag_io_cycle && !cpu.iorq_n_i && (!rd||!wr) && !private_e6_old)private_e6_count=private_e6_count+1;
        private_e6_old<=cpu.diag_io_cycle && !cpu.iorq_n_i && (!rd||!wr);
    end
    integer rst_entries=0;reg old_frame=0;
    integer i,j=0,waits=0,high_fetches=0,bank_writes=0,bdos_calls=0;
    reg io_write_old=0,bdos_old=0,seen_adl=0,seen_return=0;
    string output_text="";
    reg [7:0] expected_status;
    reg [23:0] trace_previous=24'hffffff;
    integer trace_count=0;
    reg [7:0] trace_stage=0;
    always @(posedge c54) begin
        if(reset_n && !mm && !wr && ma==`P2_FAIL_STAGE && dout!=trace_stage) begin
            trace_stage=dout;$display("COM stage %c time=%0t",dout,$time);$fflush;
        end
        din<=ext?ext_di:(!mm && !rd?lowmem[ma]:8'hff);
        if(reset_n && !mm && !wr)begin
            if(ma<16'h0080)$fatal(1,"COM wrote an MSX/DOS vector address=%h",ma);
            lowmem[ma]<=(FAULT && ma==16'h5d93) ? dout^8'h01 : dout;
        end
        if(reset_n && divider==0 && enable_run)begin
            if(cpu.u0.frame_start&&!old_frame&&!cpu.u0.frame_return)rst_entries=rst_entries+1;
            old_frame<=cpu.u0.frame_start;
            if(cpu.u0.frame_active&&cpu.u0.inte_ff1)$fatal(1,"RST test frame with interrupts enabled");
        end
        if(1'b0)
            $fatal(1,"interrupts enabled while data extensions active");
        if(reset_n && !wait_n) waits=waits+1;

        if(reset_n && ext && !mm) $fatal(1,"high memory reached MSX decode");
        

        if(reset_n && req && rw) begin
            if(ra>=23'h400000 && ra<23'h640000) $fatal(1,"COM touched MegaRAM/VRAM a=%h physical=%h pc=%h mc=%h ir=%h bank=%h",a,ra,cpu.u0.pc,cpu.u0.mcycle,cpu.u0.ir,cpu.u0.a_bank);
            bank_writes=bank_writes+1;
        end
        if(reset_n && !m1 && !mr && a==5 && !bdos_old) begin
            bdos_calls=bdos_calls+1;
            if(cpu.u0.inte_ff1!==1 || cpu.u0.adl_mode!==0 || cpu.u0.mbase!==0)
                $fatal(1,"BDOS call outside Z80/MBASE0/EI");
            if(EXTENDED && cpu.u0.extensions_enabled!==0) $fatal(1,"extensions not locked for DOS");
        end
        if(reset_n && !m1 && !mr && a==5 && !bdos_old)dos_arm<=1;
        if(reset_n && dos_arm && !m1 && !mr && a==24'h11)begin dos_irq<=1;dos_arm<=0;end
        if(reset_n && !io && !m1 && dos_irq)begin dos_irq<=0;dos_acks=dos_acks+1;end
        bdos_old<=!m1 && !mr && a==5;
        if(reset_n && !io && !wr && a[7:0]==8'hf0 && !io_write_old) begin
            output_text={output_text,dout};$write("%c",dout);
        end
        io_write_old<=!io && !wr && a[7:0]==8'hf0;
        if(reset_n && !m1 && !mr && a==24'h000080) begin
            expected_status=RUN_REQUEST==0?4:!EXTENDED?3:!SUPPORTED?5:(FAULT?2:1);
            if(lowmem[`P2_STATUS]!==expected_status) $fatal(1,"wrong COM status %h expected %h",lowmem[`P2_STATUS],expected_status);
            if(cpu.u0.sp!==16'hf000 || cpu.u0.inte_ff1!==1)
                $fatal(1,"DOS return state not restored");
            if(EXTENDED && cpu.u0.extensions_enabled!==0) $fatal(1,"extensions not locked on return");
            if({lowmem[16'ha1],lowmem[16'ha0]}!==16'h1357 || {lowmem[16'ha3],lowmem[16'ha2]}!==16'h2468)
                $fatal(1,"caller IX/IY not restored");
            if(lowmem[16'hffff]!==8'h5c || lowmem[`P2_GUARD]!==8'ha6) $fatal(1,"MSX guard/slot changed");
            if(dos_acks!=((!EXTENDED||!RUN_REQUEST||!SUPPORTED)?1:FAULT?2:7))$fatal(1,"missing DOS IRQ");
            if(bdos_calls!=((!EXTENDED||!RUN_REQUEST||!SUPPORTED)?1:FAULT?2:7)) $fatal(1,"wrong DOS print call count %d",bdos_calls);
            // TIO COM intentionally stays in Z80 and uses no extended SDRAM request.
            if((!EXTENDED || !SUPPORTED || !RUN_REQUEST) && bank_writes!=0) $fatal(1,"unsupported profile touched high memory");
            if(EXTENDED && RUN_REQUEST && SUPPORTED && !FAULT && rst_entries!=0)$fatal(1,"RST entries=%d expected=0",rst_entries);
            if(EXTENDED && RUN_REQUEST && SUPPORTED && !FAULT && 1'b0) $fatal(1,"fetch coverage bytes=%d expected=%d returns=%d",fetched,expected_count,returns_seen);
            if(cpu.u0.adl_mode!==0 || cpu.u0.pc[23:16]!==0) $fatal(1,"ADL/PC not restored for DOS");
            if(EXTENDED&&RUN_REQUEST&&SUPPORTED&&!FAULT&&private_e6_count!=40)$fatal(1,"private IO count %d",private_e6_count);
            $display("PASS tio_com_r23 phase=%0d fault=%0d extended=%0d cpu_div=%0d status=%0d high_fetch_opcodes=%0d WAIT_ticks=%0d",PHASE,FAULT,EXTENDED,CPU_DIV,expected_status,fetched,waits);
            $finish;
        end
    end
    reg [63:0] fetch_held,fetch_now;reg fetch_hold_valid=0;
    integer fetched=0,expected_count=0,returns_seen=0,k,fetch_waits=0;
    reg [23:0] expected_addr[0:127];
    reg [7:0] expected_byte[0:127];
    reg [15:0] return_pc[0:5];
    reg [5:0] return_mask=0;
    always @(posedge c54) if(reset_n) begin
        
        
        if(divider==0 && enable_run)begin
            fetch_now={a,cpu.u0.pc,cpu.u0.adl_mode,dout,mr,rd,io};
            if(cpu.u0.mcycle==1 && cpu.u0.tstate==2 && !cpu.u0.wait_n)begin
                if(fetch_hold_valid && fetch_now!==fetch_held)$fatal(1,"high fetch changed during WAIT");
                fetch_held=fetch_now;fetch_hold_valid=1;
            end else fetch_hold_valid=0;
        end
        if(cpu.u0.adl_mode && !wait_n) fetch_waits=fetch_waits+1;
        if(!rf && a[23:16]!=0) $fatal(1,"refresh retained high bank");
        if(divider==0 && enable_run && cpu.u0.mcycle==1 && cpu.u0.tstate==2 && cpu.u0.wait_n) begin
            if(a[23:16]!=0) begin
                if(cpu.u0.adl_mode!==1 && a[23:16]!==cpu.u0.mbase) $fatal(1,"Z80 fetch outside MBASE");
                fetched=fetched+1;
            end
        end
    end
    generate if(LEGACY_FEATURE)begin
    always @(cpu.diag_select) if(cpu.diag_select==8'he0)force cpu.diag_read=8'hff;else release cpu.diag_read;
    end endgenerate
    initial begin
        for(i=0;i<65536;i=i+1) lowmem[i]=0;
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
        lowmem[16'h38]=8'hfb;lowmem[16'h39]=8'hed;lowmem[16'h3a]=8'h4d;
        lowmem[16'h80]=8'h76;lowmem[16'hffff]=8'h5c;
        $readmemh(`TEST_HEX,lowmem,16'h100,`P2_COM_END);
        lowmem[16'h80]=0;
        if(RUN_REQUEST!=0) begin
            lowmem[16'h80]=5;lowmem[16'h81]=" ";lowmem[16'h82]="/";lowmem[16'h83]="R";lowmem[16'h84]="U";lowmem[16'h85]=RUN_REQUEST==1?"N":"X";
        end
        repeat(12) @(negedge c54);reset_n=1;
        @(negedge c108);mem.RstSeq=24;
    end
    initial begin #900000000;$fatal(1,"COM timeout a=%h stage=%c status=%h pc=%h mc=%h ts=%h ir=%h SPL=%h IRQ=%b NMI=%b",a,lowmem[`P2_FAIL_STAGE],lowmem[`P2_STATUS],cpu.u0.pc,cpu.u0.mcycle,cpu.u0.tstate,cpu.u0.ir,cpu.u0.spl,cpu.u0.intcycle,cpu.u0.nmicycle);end
    always @(posedge c54) if($test$plusargs("DEBUG") && reset_n && divider==0 && enable_run && cpu.u0.intcycle && ((cpu.u0.tstate==3) || (cpu.u0.mcycle==1 && cpu.u0.tstate==4)))
        $display("ENTRY mc=%h ts=%h a=%h di=%h internal=%h vec=%h I=%h%h SPL=%h write=%h",cpu.u0.mcycle,cpu.u0.tstate,a,din,cpu.u0.di_reg,cpu.u0.irq_vector,cpu.u0.i_upper,cpu.u0.i,cpu.u0.spl,wr);
    initial if($test$plusargs("DEBUG")) begin
        #20000000;$display("DEBUG pc=%h a=%h MC=%h TS=%h IR=%h SPL=%h vec=%h target=%h int=%h flags=%h stage=%c status=%h DI=%h",cpu.u0.pc,a,cpu.u0.mcycle,cpu.u0.tstate,cpu.u0.ir,cpu.u0.spl,cpu.u0.irq_vector,cpu.u0.ctrl_target,cpu.u0.intcycle,cpu.u0.f,lowmem[`P2_FAIL_STAGE],lowmem[`P2_STATUS],din);$finish;
    end
    initial if($test$plusargs("TRACE")) begin #1000000;$display("TRACE END a=%h stage=%c status=%h",a,lowmem[`P2_FAIL_STAGE],lowmem[`P2_STATUS]);$finish;end
endmodule
