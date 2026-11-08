`timescale 1ns/1ps
// Isolated request-register test; CPU execution itself is covered by the COM suites.
module tb_msx_request_r11_3;
    parameter DIAGNOSTICS=0, FAULT=0;
    reg clk=0,reset_n=0,fall_enable=0;
    always #10 clk=~clk;
    reg [7:0] bank=0;
    reg [15:0] address=0;
    reg [2:0] ts=1,mc=1;
    reg io=0,intcycle_n=1,refresh_n=1,write_intent=0,active=0;
    wire [23:0] a;
    wire [15:0] msx_a;
    wire ew;
    G80A_eZ80 cpu(.RESET_n(reset_n),.CLK_n(clk),.clk_enable(1'b0),.clk_falling(fall_enable),
        .WAIT_n(1'b0),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(8'h00),
        .A24(a),.A_MSX(msx_a),.Extended_Window(ew));
    wire mm,ext,wait_n,req,rw;
    wire [15:0] ma;
    wire [22:0] ra;
    wire [7:0] di,wd;
    ez80_memory_bridge #(.REQUEST_BANK_QUALIFIED(1),.PREDECODED_MSX(1)) bridge(
        .clk(clk),.reset_n(reset_n),.cpu_addr(a),.cpu_mreq_n(1'b0),
        .cpu_iorq_n(!io),.cpu_rfsh_n(refresh_n),.cpu_rd_n(1'b1),.cpu_wr_n(1'b1),.cpu_dout(8'h00),
        .cpu_msx_addr(msx_a),.cpu_extended_window(ew),.msx_mreq_n(mm),.msx_addr(ma),
        .extended_cycle(ext),.wait_n(wait_n),.cpu_din(di),.ram_req(req),.ram_write(rw),
        .ram_addr(ra),.ram_din(wd),.ram_done(1'b0),.ram_dout(8'h00));
    generate if(DIAGNOSTICS)begin initial force cpu.diag_active=active;end endgenerate
    integer b,k,kind,n,checks=0;
    reg [15:0] offsets[0:7];
    reg [23:0] expected,held;
    task check(input [23:0] want);
        begin
            #0.01;
            if(a!==want) $fatal(1,"request qualification actual %h expected %h",a,want);
            if(ma!==(want[23:16]!=0?16'h0000:want[15:0]) || mm!==(want[23:16]!=0))
                $fatal(1,"MSX isolation actual=%h/%b address=%h",ma,mm,want);
            checks=checks+1;
        end
    endtask
    initial begin
        force cpu.bank_i=bank;force cpu.a_i=address;force cpu.tstate=ts;
        force cpu.mcycle=mc;force cpu.iorq=io;force cpu.intcycle_n=intcycle_n;
        force cpu.rfsh_n_i=refresh_n;force cpu.write=write_intent;
        force cpu.busak_n_i=1'b1;
        offsets[0]=0;offsets[1]=16'h0038;offsets[2]=16'h0066;offsets[3]=16'h007f;
        offsets[4]=16'h0080;offsets[5]=16'h4000;offsets[6]=16'hfffe;offsets[7]=16'hffff;
        repeat(3) @(posedge clk);reset_n=1;
        if(FAULT==1)force cpu.request_msx_address=16'hffff;
        if(FAULT==2)force cpu.request_extended=1'b0;
        if(FAULT==3)force cpu.request_address=24'h0f0000;
        for(b=0;b<256;b=b+1)for(k=0;k<8;k=k+1)for(kind=0;kind<8;kind=kind+1)begin
            @(posedge clk);bank=b;address=offsets[k];ts=1;mc=(kind==4 ? 2:1);
            io=(kind==2);intcycle_n=!(kind==3 || kind==4);refresh_n=1;
            write_intent=(kind==1 || kind==7);active=(kind==6 || kind==7);fall_enable=1;
            expected={bank,address};
            if(io || (!intcycle_n && mc==1)) expected={8'h00,address};
            else if(DIAGNOSTICS && active && !bank && address<128 && !write_intent && intcycle_n)
                expected={8'h0f,address};
            @(negedge clk);check(expected);held=expected;
            // WAIT/T2 and CEN pause must retain the complete ordinary request,
            // even if upstream address/intent changes for unrelated internal work.
            @(posedge clk);ts=2;bank=~bank;address=~address;io=~io;write_intent=~write_intent;active=~active;
            repeat(2)begin @(negedge clk);check(held);end
            @(posedge clk);ts=1;fall_enable=0;
            repeat(2)begin @(negedge clk);check(held);end
            if(kind==5)begin
                // Refresh temporarily exposes bank zero and the refresh address;
                // the ordinary held request must reappear afterwards.
                @(posedge clk);refresh_n=0;check({8'h00,address});
                @(posedge clk);refresh_n=1;check(held);
            end
        end
        $display("PASS MSX request R11.3 diagnostics=%0d checks=%0d",DIAGNOSTICS,checks);$finish;
    end
endmodule
