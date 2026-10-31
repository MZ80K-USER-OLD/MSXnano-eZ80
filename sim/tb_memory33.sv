`timescale 1ns/1ps
module tb_memory33;
    parameter PHASE=0, SKIP_INIT=1;
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
    reg [23:0] a=0;
    reg mr=1,rd=1,wr=1,rf=1;
    reg [7:0] dout=0;
    wire mm,ext,wait_n,req,rw,done;
    wire [15:0] ma;
    wire [22:0] ra;
    wire [7:0] di,wd,ramdata;
    ez80_memory_bridge bridge(c54,reset_n,a,mr,1'b1,rf,rd,wr,dout,
        mm,ma,ext,wait_n,di,req,rw,ra,wd,done,ramdata);
    reg mapper_req=0,mapper_write=0,mega_req=0,mega_write=0;
    reg [21:0] mapper_addr=0;
    reg [20:0] mega_addr=0;
    reg [7:0] legacy_din=0;
    reg [16:0] va=0;
    reg vw=0;
    reg [7:0] vd=0;
    wire [15:0] vo;
    wire [7:0] mo,go;
    wire cs,ras,cas,we,sc,cke;
    wire [31:0] dq;
    wire [10:0] sa;
    wire [1:0] ba;
    wire [3:0] dm;
    memory_ctrl_ez80 mem(
        .clk_27m(c54),.clk_108m(c108),.bus_reset_n(reset_n),
        .video_dhclk(dh),.video_dlclk(dl),.mapper_din(legacy_din),
        .mapper_req(mapper_req),.mapper_write(mapper_write),.mapper_addr(mapper_addr),
        .megaram_req(mega_req),.megaram_write(mega_write),.megaram_addr(mega_addr),
        .vram_addr(va),.vram_write(vw),.vram_din(vd),.bus_rfsh_n(rf),
        .mapper_dout(mo),.megaram_dout(go),.vram_dout(vo),
        .ext_req(req),.ext_write(rw),.ext_addr(ra),.ext_din(wd),.ext_done(done),.ext_dout(ramdata),
        .O_sdram_clk(sc),.O_sdram_cke(cke),.O_sdram_cs_n(cs),.O_sdram_ras_n(ras),
        .O_sdram_cas_n(cas),.O_sdram_wen_n(we),.IO_sdram_dq(dq),
        .O_sdram_addr(sa),.O_sdram_ba(ba),.O_sdram_dqm(dm));
    sdram_model33 ram(sc,{cs,ras,cas,we},sa,ba,dm,dq);
    integer n,k,b,transactions=0,timeout,before_write,waits=0,video_reads=0,video_waits=0;
    reg [23:0] targets[0:255];
    reg [7:0] values[0:255],got;
    integer count=0;
    task tick; begin @(posedge c54);#1;end endtask
    task pause;begin repeat(24) tick;end endtask
    task transfer(input [23:0] address,input bit writing,input [7:0] data,input [7:0] expected);
        begin
            @(negedge c54); a=address;mr=0;rd=writing;wr=!writing;dout=data;
            #1;before_write=ram.writes;timeout=0;
            while(!wait_n && timeout<300) begin tick;timeout=timeout+1;waits=waits+1;end
            if(timeout==300) $fatal(1,"memory timeout addr %h state %d/%b/%b",address,bridge.state,mem.ext_selected,mem.ff_sdr_seq);
            if(mm!==1) $fatal(1,"MSX window not isolated");
            if(!writing && di!==expected) $fatal(1,"memory read %h got %h expected %h",address,di,expected);
            if(writing && ram.writes-before_write!==1) $fatal(1,"write count %h delta %d",address,ram.writes-before_write);
            repeat(24) tick;
            if(writing && ram.writes-before_write!==1) $fatal(1,"write repeated while CPU holds request");
            @(negedge c54);mr=1;rd=1;wr=1;
            repeat(8) tick;
            transactions=transactions+1;
        end
    endtask
    always @(posedge c108) if(reset_n && mem.RstSeq>=24) begin
        if(mem.ff_sdr_seq==2 && dl && mem.SdrSta[2:1]!=2'b11)
            $fatal(1,"extension stole VDP slot");
        if({cs,ras,cas,we}==4'b0101 && mem.SdrSta[1]) begin
            video_reads=video_reads+1;
            if(req && !wait_n) video_waits=video_waits+1;
        end
    end
    initial begin
        repeat(12) tick;reset_n=1;
        // Skip only the long power-on SDRAM initialization in this functional fixture.
        @(negedge c108);
        if(SKIP_INIT) mem.RstSeq=24;
        else begin
            // Hold a real request across the complete SDRAM startup delay.
            @(negedge c54);a=24'h010abc;mr=0;rd=0;wr=1;
            repeat(100) tick;
            if(wait_n || !req || done || mem.ext_selected)
                $fatal(1,"request accepted before SDRAM initialization");
            wait(mem.RstSeq>=24);
            timeout=0;
            while(!wait_n && timeout<300) begin tick;timeout=timeout+1;end
            if(!wait_n || di!==8'h00) $fatal(1,"startup pending request failed");
            @(negedge c54);mr=1;rd=1;repeat(8) tick;
            transactions=transactions+1;
        end
        repeat(40+PHASE) tick;
        // Every mapped bank and all four byte lanes, including FFFF slot-register aliases.
        for(b=1;b<=99;b=b+1) if(b<=27 || b>=64) begin
            for(k=0;k<4;k=k+1) begin
                targets[count]={b[7:0],16'hfffc+k[15:0]};
                values[count]=b*7+k+1;
                transfer(targets[count],1,values[count],0);count=count+1;
            end
        end
        for(n=count-1;n>=0;n=n-1) transfer(targets[n],0,0,values[n]);
        // VDP alias readback and byte-order: lower/upper 64 KiB share adjacent lanes.
        va=17'h01234;
        transfer(24'h601234,1,8'h56,0);transfer(24'h611234,1,8'hab,0);
        pause;if(vo!==16'hab56) $fatal(1,"VDP alias read got %h",vo);
        // VDP write to both logical halves, then CPU readback (CPU does not steal VDP slots).
        vd=8'h39;vw=1;pause;vw=0;pause;transfer(24'h601234,0,0,8'h39);
        va=17'h11234;vd=8'he2;vw=1;pause;vw=0;pause;transfer(24'h611234,0,0,8'he2);
        // Reserved 62/63 must not alias VDP 60/61.
        transfer(24'h621234,1,8'h77,0);transfer(24'h631234,1,8'h88,0);
        transfer(24'h601234,0,0,8'h39);transfer(24'h611234,0,0,8'he2);
        transfer(24'h621234,0,0,8'h77);transfer(24'h631234,0,0,8'h88);
        // Shared MegaRAM through the existing mapper path, both directions.
        transfer(24'h401234,1,8'ha9,0);mega_addr=21'h1234;mega_req=1;pause;
        if(go!==8'ha9) $fatal(1,"legacy MegaRAM alias got %h",go);
        mega_req=0;pause;mega_write=1;legacy_din=8'hb7;mega_req=1;pause;
        mega_req=0;mega_write=0;pause;transfer(24'h401234,0,0,8'hb7);
        // Actual bank-00 slot/mapper RAM path is separate from private RAM.
        mapper_addr=22'h1234;mapper_req=1;mapper_write=1;legacy_din=8'h5c;pause;
        mapper_req=0;mapper_write=0;pause;mapper_req=1;pause;
        if(mo!==8'h5c) $fatal(1,"legacy mapper read got %h",mo);
        mapper_req=0;pause;
        // Refresh continues independently of pending CPU work.
        rf=0;pause;rf=1;pause;
        if(ram.refreshes==0 || video_waits==0 || waits==0) $fatal(1,"missing refresh/VDP contention/WAIT");
        // Reset a captured request before the 108 MHz receiver can accept it.
        @(negedge c54);a=24'h010abc;dout=8'hdd;mr=0;wr=0;rd=1;
        tick;if(!req) $fatal(1,"reset fixture request missing");
        @(negedge c108);reset_n=0;mr=1;wr=1;rd=1;
        repeat(6) tick;reset_n=1;
        @(negedge c108);mem.RstSeq=24;
        repeat(40) tick;
        transfer(24'h010abc,0,0,8'h00);
        $display("PASS memory33 phase=%0d transactions=%0d WAIT_ticks=%0d VDP_reads=%0d contended=%0d refresh=%0d",PHASE,transactions,waits,video_reads,video_waits,ram.refreshes);
        $finish;
    end
    initial begin #100000000;$fatal(1,"global timeout");end
endmodule
