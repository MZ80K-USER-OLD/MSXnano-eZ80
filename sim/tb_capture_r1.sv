`timescale 1ns/1ps
// Pin schedule comparison. Old read-latch values are intentionally not compared:
// memory.v reads its Z-valued output register, the new fork reads the DQ pad net.
module tb_capture_r1;
    parameter PHASE=0;
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
    reg mr=0,mw=0,gr=0,gw=0,vw=0,rf=1;
    reg [21:0] ma=0;
    reg [20:0] ga=0;
    reg [16:0] va=0;
    reg [7:0] data=0,vd=0;
    wire [3:0] cmd0,cmd1,dm0,dm1;
    wire [10:0] a0,a1;
    wire [1:0] ba0,ba1;
    wire [31:0] dq0,dq1;
    memory_ctrl oldmem(.clk_27m(c54),.clk_108m(c108),.bus_reset_n(reset_n),
        .video_dhclk(dh),.video_dlclk(dl),.mapper_din(data),
        .mapper_req(mr),.mapper_write(mw),.mapper_addr(ma),
        .megaram_req(gr),.megaram_write(gw),.megaram_addr(ga),
        .vram_addr(va),.vram_write(vw),.vram_din(vd),.bus_rfsh_n(rf),
        .O_sdram_cs_n(cmd0[3]),.O_sdram_ras_n(cmd0[2]),.O_sdram_cas_n(cmd0[1]),
        .O_sdram_wen_n(cmd0[0]),.IO_sdram_dq(dq0),.O_sdram_addr(a0),.O_sdram_ba(ba0),.O_sdram_dqm(dm0));
    memory_ctrl_ez80 newmem(.clk_27m(c54),.clk_108m(c108),.bus_reset_n(reset_n),
        .video_dhclk(dh),.video_dlclk(dl),.mapper_din(data),
        .mapper_req(mr),.mapper_write(mw),.mapper_addr(ma),
        .megaram_req(gr),.megaram_write(gw),.megaram_addr(ga),
        .vram_addr(va),.vram_write(vw),.vram_din(vd),.bus_rfsh_n(rf),
        .ext_req(1'b0),.ext_write(1'b0),.ext_addr(23'h0),.ext_din(8'h0),
        .O_sdram_cs_n(cmd1[3]),.O_sdram_ras_n(cmd1[2]),.O_sdram_cas_n(cmd1[1]),
        .O_sdram_wen_n(cmd1[0]),.IO_sdram_dq(dq1),.O_sdram_addr(a1),.O_sdram_ba(ba1),.O_sdram_dqm(dm1));

    integer n,checked=0;
    reg [7:0] expected;
    reg [22:0] addr_expected;
    always @(negedge c108) if(reset_n && cmd1==4'b0100 && newmem.SdrSta==3'b101) begin
        if(dq1!=={4{expected}}) $fatal(1,"live upstream data reached SDRAM expected=%h got=%h",expected,dq1);
        if(newmem.cpu_sdram_addr!==addr_expected) $fatal(1,"live upstream address reached SDRAM");
        checked=checked+1;
    end
    initial begin
        repeat(12) @(negedge c54);reset_n=1;
        @(negedge c108);newmem.ff_sdr_seq=0;newmem.ff_mem_seq=0;newmem.SdrSta=0;newmem.RstSeq=24;
        repeat(PHASE) @(negedge c54);
        for(n=0;n<16;n=n+1) begin
            @(negedge c54);ma=22'h12340+n;ga=21'h34560+n;data=8'h90+n;expected=data;
            mr=!(n%2);gr=n%2;mw=mr;gw=gr;
            addr_expected=mr?{1'b0,ma}:{2'b10,ga};
            wait(newmem.sdram_seq==2);#1;
            // Payload changes are AFTER the documented latch edge.
            data=~expected;ma=22'h3fffff;ga=21'h1fffff;
            wait(newmem.sdram_seq==4);
            @(negedge c54);mr=0;gr=0;mw=0;gw=0;
            repeat(20) @(negedge c54);
        end
        if(checked!=16) $fatal(1,"capture write count %0d",checked);
        $display("PASS capture R1 phase=%0d held payload writes=%0d",PHASE,checked);$finish;
    end
    initial begin #1000000;$fatal(1,"capture timeout");end
endmodule
