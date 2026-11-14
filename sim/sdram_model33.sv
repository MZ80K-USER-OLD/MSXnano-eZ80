`timescale 1ns/1ps
// Functional BL=1, CL=2 model. Checks bank/row/column and DQM lanes.
// This is not a device timing or retention sign-off model.
module sdram_model33(input clk,input [3:0] cmd,input [10:0] a,input [1:0] ba,
    input [3:0] dqm,inout [31:0] dq);
    reg [31:0] words[0:2097151];
    reg [10:0] row[0:3];
    reg [3:0] active=0;
    reg [31:0] r0,r1,read_data;
    reg p0=0,p1=0,drive=0;
    integer reads=0,writes=0,refreshes=0,lane,index;
    reg [31:0] value;
    assign dq=drive?read_data:32'bz;
    function [31:0] clean(input [31:0] x);
        integer j;begin
            for(j=0;j<4;j=j+1) clean[j*8+:8]=(^x[j*8+:8]===1'bx)?8'h00:x[j*8+:8];
        end
    endfunction
    always @(posedge clk) begin
        p0<=0;p1<=p0;drive<=p1;r1<=r0;read_data<=r1;
        case(cmd)
            4'b0011: begin row[ba]<=a;active[ba]<=1;end
            4'b0101,4'b0100: begin
                if(!active[ba]) $fatal(1,"SDRAM column command without active bank");
                if(!a[10] || a[9:8]!=0) $fatal(1,"SDRAM column/auto-precharge");
                index={ba,a[7:0],row[ba]};
                if(cmd==4'b0101) begin reads=reads+1;r0<=clean(words[index]);p0<=1;end
                else begin
                    value=clean(words[index]);
                    for(lane=0;lane<4;lane=lane+1) if(!dqm[lane]) begin
                        if((^dq[lane*8+:8])===1'bx) $fatal(1,"invalid write data");
                        value[lane*8+:8]=dq[lane*8+:8];
                    end
                    words[index]=value;writes=writes+1;
                end
                active[ba]<=0;
            end
            4'b0010: active<=0;
            4'b0001: begin refreshes=refreshes+1;active<=0;end
            default: ;
        endcase
    end
endmodule
