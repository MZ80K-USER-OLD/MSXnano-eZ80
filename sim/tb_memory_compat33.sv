`timescale 1ns/1ps
// Pin schedule comparison. Old read-latch values are intentionally not compared:
// memory.v reads its Z-valued output register, the new fork reads the DQ pad net.
module tb_memory_compat33;
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
    bit checking=0;
    integer edges=0,i,k;
    always @(negedge c108) if(checking) begin
        if({cmd0,dm0,a0,ba0,dq0}!=={cmd1,dm1,a1,ba1,dq1})
            $fatal(1,"legacy pin mismatch phase=%0d seq=%b oldcmd=%b newcmd=%b",PHASE,oldmem.ff_sdr_seq,cmd0,cmd1);
        edges=edges+1;
    end
    task pause;begin repeat(80) @(negedge c54);end endtask
    initial begin
        repeat(12) @(negedge c54);reset_n=1;
        // The old controller lacks simulation reset for these phase registers.
        @(negedge c108);
        oldmem.ff_sdr_seq=0;oldmem.ff_mem_seq=0;oldmem.SdrSta=0;
        newmem.ff_sdr_seq=0;newmem.ff_mem_seq=0;newmem.SdrSta=0;
        oldmem.RstSeq=24;newmem.RstSeq=24;
        pause;checking=1;
        repeat(PHASE) @(negedge c54);
        for(i=0;i<16;i=i+1) begin
            ma=(22'h3fffc0+i*4);ga=(21'h1fffc0+i*4);va=17'hffff+i;
            for(k=0;k<4;k=k+1) begin
                ma[1:0]=k;ga[1:0]=k;data=i*13+k;vd=i*7+k;
                mr=1;mw=1;pause;mr=0;mw=0;pause;mr=1;pause;mr=0;pause;
                gr=1;gw=1;pause;gr=0;gw=0;pause;gr=1;pause;gr=0;pause;
                vw=1;pause;vw=0;pause;rf=0;pause;rf=1;pause;
            end
        end
        $display("PASS memory_compat33 phase=%0d identical SDRAM pin edges=%0d",PHASE,edges);$finish;
    end
endmodule
