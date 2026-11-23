// R24.5 normal build: identical observation-only interface, no monitor state.
// The UART diagnostic GPRJ selects the original msx2p_debug.v instead.
module msx2p_debug(
    input clk_27m, input clk, input clk_enable, input reset_n,
    input [15:0] bus_addr, input [7:0] bus_data,
    input bus_iorq_n, input bus_mreq_n, input bus_rd_n, input bus_wr_n,
    input send,
    output uart_tx, output boot_ok
);
    // Retain the physical TX port and CST assignment. UART idle is high.
    assign uart_tx = 1'b1;
    assign boot_ok = 1'b0; // Existing top leaves this observation output open.
endmodule
