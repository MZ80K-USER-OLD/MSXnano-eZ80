// R21.3: observation byte selection stays on the Verilog side.
// FD/FE test the same eight-bit connection as the recorded data.
module ez80_trace_mux(input wire [63:0] record_data,
    input wire [3:0] selector, output reg [7:0] byte_data);
    always @* begin
        case (selector)
            4'h0: byte_data=record_data[7:0];
            4'h1: byte_data=record_data[15:8];
            4'h2: byte_data=record_data[23:16];
            4'h3: byte_data=record_data[31:24];
            4'h4: byte_data=record_data[39:32];
            4'h5: byte_data=record_data[47:40];
            4'h6: byte_data=record_data[55:48];
            4'h7: byte_data=record_data[63:56];
            4'hd: byte_data=8'h55;
            4'he: byte_data=8'haa;
            default: byte_data=8'h00;
        endcase
    end
endmodule
