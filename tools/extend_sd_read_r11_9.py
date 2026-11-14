from pathlib import Path
r=Path(__file__).resolve().parent.parent;p=r/'fpga/top_ez80.v';s=p.read_text()
s=s.replace('    reg sd_cs_w;\n    always @ (posedge clk_27m) begin\n','''    reg sd_cs_w;
    // R11.9: read register number travels with the existing SD select stage.
    // The CPU holds the MSX request through the data sampling point.
    reg [7:0] sd_read_index;
    always @ (posedge clk_27m) begin
        sd_read_index <= bus_addr[7:0];
''',1)
a=s.index('                if (~bus_rd_n) begin\n                    case(bus_addr)',s.index('    reg [7:0] ff_sd_cd;'))
b=s.index('                    endcase',a)
part=s[a:b].replace('case(bus_addr)','case({8\'h7E, sd_read_index})',1);s=s[:a]+part+s[b:]
p.write_text(s)
