// v33: isolate the MSX window before any 16-bit memory decode.
// The external data bus remains byte-wide. Width/suffix handling is in the CPU.
module ez80_memory_bridge #(
    // Enable only with the R11.1 wrapper, which forces bank zero for I/O/IACK/refresh.
    parameter REQUEST_BANK_QUALIFIED = 0,
    parameter PREDECODED_MSX = 0,
    parameter TRACE_MEMORY = 0
) (
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
    input wire [7:0] ram_dout,
    // Only enable PREDECODED_MSX with the R11.3 wrapper's registered outputs.
    input wire [15:0] cpu_msx_addr,
    input wire cpu_extended_window,
    output wire [63:0] memory_trace
);
    wire [7:0] bank = cpu_addr[23:16];
    wire extended_window = PREDECODED_MSX ? cpu_extended_window : bank != 8'h00 &&
        (REQUEST_BANK_QUALIFIED || (cpu_iorq_n && cpu_rfsh_n));
    assign msx_mreq_n = cpu_mreq_n | extended_window;
    assign msx_addr = PREDECODED_MSX ? cpu_msx_addr : extended_window ? 16'h0000 : cpu_addr[15:0];
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
    // R23.3: local full-rate sampling removes the CPU falling-edge strobe
    // from the multi-LUT payload capture enable. WAIT below stays immediate.
    // Address/data remain held by the CPU until COMPLETE releases WAIT.
    reg sampled_mreq_n, sampled_rd_n, sampled_wr_n, sampled_window;
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            sampled_mreq_n<=1; sampled_rd_n<=1;
            sampled_wr_n<=1; sampled_window<=0;
        end else begin
            sampled_mreq_n<=cpu_mreq_n; sampled_rd_n<=cpu_rd_n;
            sampled_wr_n<=cpu_wr_n; sampled_window<=extended_window;
        end
    end
    wire sampled_cycle = sampled_window && !sampled_mreq_n &&
                         (!sampled_rd_n || !sampled_wr_n);
    // Live MREQ/window cancel stale samples without using live RD/WR in
    // the capture enable. MREQ is asserted in T1, before WR in T2.
    wire accept_request = state==IDLE && sampled_cycle &&
                          extended_window && !cpu_mreq_n && mapped && !done_sync;

    // R21.2 observation only: retain the last accepted extended write.
    // The read record reuses the existing request address/result registers.
    generate if (TRACE_MEMORY) begin: trace_memory
        reg [30:0] last_write;
        always @(posedge clk or negedge reset_n) begin
            if (!reset_n) last_write<=0;
            else if (accept_request && !sampled_wr_n)
                last_write<={physical_addr,cpu_dout};
        end
        assign memory_trace={1'b0,ram_addr,result,1'b0,last_write};
    end else begin: no_trace_memory
        assign memory_trace=64'b0;
    end endgenerate
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
                IDLE: if (accept_request) begin
                    ram_addr<=physical_addr; ram_din<=cpu_dout;
                    ram_write<=!sampled_wr_n; ram_req<=1; state<=WAIT_RAM;
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
