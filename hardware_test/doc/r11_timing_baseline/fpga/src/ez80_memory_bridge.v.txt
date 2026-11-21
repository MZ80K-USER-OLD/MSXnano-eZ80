// v33: isolate the MSX window before any 16-bit memory decode.
// The external data bus remains byte-wide. Width/suffix handling is in the CPU.
module ez80_memory_bridge (
    input wire clk, reset_n,
    input wire [23:0] cpu_addr,
    input wire cpu_mreq_n, cpu_iorq_n, cpu_rfsh_n, cpu_rd_n, cpu_wr_n,
    input wire [7:0] cpu_dout,
    output wire msx_mreq_n,
    output wire [15:0] msx_addr,
    output wire extended_cycle,
    output wire wait_n,
    output wire [7:0] cpu_din,
    output reg ram_req,
    output reg ram_write,
    output reg [22:0] ram_addr,
    output reg [7:0] ram_din,
    input wire ram_done,
    input wire [7:0] ram_dout
);
    wire [7:0] bank = cpu_addr[23:16];
    wire extended_window = bank != 8'h00 && cpu_iorq_n && cpu_rfsh_n;
    assign msx_mreq_n = cpu_mreq_n | extended_window;
    assign msx_addr = extended_window ? 16'h0000 : cpu_addr[15:0];
    assign extended_cycle = extended_window && !cpu_mreq_n &&
                            (!cpu_rd_n || !cpu_wr_n);
    wire private_ram = bank >= 8'h01 && bank <= 8'h1b;
    wire mega_ram = bank >= 8'h40 && bank <= 8'h5f;
    wire video_ram = bank >= 8'h60 && bank <= 8'h63;
    wire mapped = private_ram || mega_ram || video_ram;
    // VDP storage: row=V[10:0], column=V[15:11], lane=V[16].
    // The reserved second 128 KiB uses lanes 2/3 (V[17]=1).
    wire [22:0] physical_addr = private_ram ?
        (23'h640000 + {bank[6:0],cpu_addr[15:0]}) : video_ram ?
        {5'b11000,cpu_addr[15:0],cpu_addr[17:16]} : cpu_addr[22:0];
    localparam IDLE=2'd0, WAIT_RAM=2'd1, COMPLETE=2'd2, DRAIN=2'd3;
    reg [1:0] state;
    reg done_meta, done_sync;
    reg [7:0] result;
    // ram_dout is held by the memory controller until the next request.
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin done_meta<=0; done_sync<=0; end
        else begin done_meta<=ram_done; done_sync<=done_meta; end
    end
    // WR is asserted at the edge where G80A samples WAIT. Request WAIT from
    // MREQ/T1, before the write strobe, so a write cannot escape into T3 early.
    wire extended_memory_request = extended_window && !cpu_mreq_n;
    assign wait_n = !(extended_memory_request && mapped && state != COMPLETE);
    assign cpu_din = extended_cycle && mapped && state == COMPLETE ? result : 8'hff;
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            state<=IDLE; ram_req<=0; ram_write<=0;
            ram_addr<=0; ram_din<=0; result<=8'hff;
        end else begin
            case (state)
                IDLE: if (extended_cycle && mapped && !done_sync) begin
                    ram_addr<=physical_addr; ram_din<=cpu_dout;
                    ram_write<=!cpu_wr_n; ram_req<=1; state<=WAIT_RAM;
                end
                WAIT_RAM: if (done_sync) begin
                    result<=ram_dout; ram_req<=0; state<=COMPLETE;
                end
                COMPLETE: if (!extended_cycle) begin
                    if (!done_sync) state<=IDLE; else state<=DRAIN;
                end
                DRAIN: if (!done_sync) state<=IDLE;
                default: begin ram_req<=0; state<=IDLE; end
            endcase
        end
    end
endmodule
