// R22.3 observation-only monitor. Never releases WAIT or modifies a request.
// LED outputs are active low on Tang Nano 20K.
module ez80_wait_monitor #(
    parameter AGE_BITS=20,       // 2^20 / 54 MHz = 19.4 ms
    parameter DEBOUNCE_BITS=20,
    parameter DISPLAY_TICKS=27000000 // page index for 0.5 seconds
) (
    input wire clk, reset_n, button,
    input wire [23:0] cpu_addr,
    input wire [22:0] ram_addr,
    input wire mreq_n, rd_n, wr_n, extended_window, wait_n,
    input wire ram_req, ram_write, ram_done, wait_io,
    input wire [4:0] bridge_debug,
    input wire [3:0] controller_debug,
    output wire [5:0] led_n,
    output reg captured,
    output reg [63:0] snapshot
);
    reg [AGE_BITS-1:0] age;
    reg button_meta, button_sync, button_stable;
    reg [DEBOUNCE_BITS-1:0] debounce;
    reg [3:0] controller_meta, controller_sync;
    reg [3:0] page;
    reg [25:0] display_timer;
    wire button_press = (&debounce) && button_sync && !button_stable;
    // Monitor the full extended MREQ duration, including COMPLETE with WAIT high.
    // No MREQ: no timeout, even if the address is nonzero during an internal cycle.
    wire active_request = extended_window && !mreq_n && bridge_debug[4];
    wire [63:0] live_snapshot = {
        wait_io, ram_addr, cpu_addr, controller_sync,
        extended_window, wr_n, rd_n, mreq_n,
        bridge_debug[3], bridge_debug[2], wait_n, ram_write,
        ram_done, ram_req, bridge_debug[1:0]
    };
    // LED5=latched. LED4=1 for data, 0 for page index. LED3..0=hex digit.
    wire showing_data = display_timer >= DISPLAY_TICKS;
    wire [3:0] digit = showing_data ? (snapshot >> {page,2'b00}) : page;
    assign led_n = captured ? ~{1'b1,showing_data,digit}
                            : ~{display_timer[24],5'b00000};
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            age<=0; captured<=0; snapshot<=0;
            button_meta<=0; button_sync<=0; button_stable<=0; debounce<=0;
            controller_meta<=0; controller_sync<=0; page<=0; display_timer<=0;
        end else begin
            button_meta<=button; button_sync<=button_meta;
            controller_meta<=controller_debug; controller_sync<=controller_meta;
            if (button_sync==button_stable) debounce<=0;
            else if (&debounce) begin button_stable<=button_sync; debounce<=0; end
            else debounce<=debounce+1'b1;
            if (!captured) begin
                display_timer<=display_timer+1'b1;
                if (!active_request) age<=0;
                else if (&age) begin
                    snapshot<=live_snapshot; captured<=1; page<=0; display_timer<=0;
                end else age<=age+1'b1;
            end else if (button_press) begin
                page<=page+1'b1; display_timer<=0;
            end else if (!showing_data) display_timer<=display_timer+1'b1;
        end
    end
endmodule
