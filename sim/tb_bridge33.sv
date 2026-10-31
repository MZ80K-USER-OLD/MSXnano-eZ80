`timescale 1ns/1ps
module tb_bridge33;
    reg clk=0, reset_n=0;
    always #10 clk=~clk;
    reg [23:0] a=0;
    reg mr=1,io=1,rf=1,rd=1,wr=1;
    reg [7:0] dout=0;
    wire mm,ext,wait_n,req,rw;
    wire [15:0] ma;
    wire [22:0] ra;
    wire [7:0] di,wd;
    reg done=0;
    reg [7:0] ramdata=0;
    ez80_memory_bridge dut(clk,reset_n,a,mr,io,rf,rd,wr,dout,
        mm,ma,ext,wait_n,di,req,rw,ra,wd,done,ramdata);
    integer bank,k,op,checks=0,timeout;
    reg [15:0] offset[0:7];
    reg [22:0] expected;
    reg mapped;
    task tick; begin @(posedge clk); #1; end endtask
    task idle; begin
        @(negedge clk);mr=1;rd=1;wr=1;done=0;
        repeat(6) tick;
        if(req) $fatal(1,"request not retired");
    end endtask
    initial begin
        offset[0]=0;offset[1]=1;offset[2]=2;offset[3]=3;
        offset[4]=16'h3fff;offset[5]=16'h7fff;offset[6]=16'hfffe;offset[7]=16'hffff;
        repeat(3) tick;reset_n=1;
        for(bank=0;bank<256;bank=bank+1) begin
            for(k=0;k<8;k=k+1) begin
                for(op=0;op<2;op=op+1) begin
                    @(negedge clk);a={bank[7:0],offset[k]};mr=0;io=1;rf=1;
                    rd=op;wr=!op;dout=(bank^k^8'ha5);
                    mapped=(bank>=1 && bank<=27)||(bank>=64 && bank<=99);
                    expected=bank>=1 && bank<=27 ? 23'h640000+a :
                             bank>=96 && bank<=99 ? 23'h600000+offset[k]*4+(bank-96) : a;
                    #1;
                    if(mm !== (bank!=0) || ma !== (bank!=0?16'h0000:offset[k]))
                        $fatal(1,"MSX isolation bank=%h offset=%h",bank,offset[k]);
                    if(!mapped) begin
                        repeat(5) tick;
                        if(req || !wait_n || di!==8'hff) $fatal(1,"unmapped request bank %h",bank);
                    end else begin
                        if(wait_n) $fatal(1,"WAIT absent before capture");
                        tick;
                        if(!req || ra!==expected || rw!==op[0] || wd!==dout)
                            $fatal(1,"decode bank=%h offset=%h got=%h expected=%h",bank,offset[k],ra,expected);
                        repeat(7) begin tick;
                            if(!req || wait_n || ra!==expected || wd!==dout || rw!==op[0])
                                $fatal(1,"request changed while waiting");
                        end
                        @(negedge clk);ramdata=bank^k;done=1;
                        timeout=0;
                        while(!wait_n && timeout<8) begin tick;timeout=timeout+1;end
                        if(!wait_n || req || di!==(bank[7:0]^k[7:0])) $fatal(1,"completion mismatch");
                        repeat(10) begin tick;if(req || !wait_n) $fatal(1,"duplicate request");end
                    end
                    checks=checks+1;idle;
                end
                // High addresses must not turn I/O, refresh or acknowledge into RAM.
                @(negedge clk);mr=1;io=0;rf=1;rd=0;wr=1;#1;
                if(mm!==1 || ma!==offset[k] || ext || req || !wait_n) $fatal(1,"I/O decode");
                checks=checks+1;idle;
                @(negedge clk);mr=0;io=1;rf=0;rd=1;wr=1;#1;
                if(mm!==0 || ma!==offset[k] || ext || req || !wait_n) $fatal(1,"refresh decode");
                checks=checks+1;idle;
                @(negedge clk);mr=1;io=0;rf=1;rd=1;wr=1;#1;
                if(ext || req || !wait_n) $fatal(1,"ack decode");
                checks=checks+1;idle;
            end
        end
        // Cancellation by reset must clear a pending transaction.
        @(negedge clk);a=24'h010000;mr=0;rd=0;wr=1;io=1;rf=1;
        repeat(4) tick;if(!req || wait_n) $fatal(1,"reset setup");
        reset_n=0;tick;if(req) $fatal(1,"reset did not cancel request");
        $display("PASS bridge33 %0d decode/handshake checks plus reset",checks);
        $finish;
    end
endmodule
