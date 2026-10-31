"""Create the eZ80 controller fork; keep the original MSX controller unchanged."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
s=(r/'fpga/src/memory.v').read_text()
s=s.replace('module memory_ctrl (','''// v33: dedicated CPU slots, four-phase held request/acknowledge.
// VDP slots and refresh selection retain the original schedule.
module memory_ctrl_ez80 (
    input wire ext_req, ext_write,
    input wire [22:0] ext_addr,
    input wire [7:0] ext_din,
    output reg ext_done,
    output reg [7:0] ext_dout,''',1)
pos=s.index('    always @ (posedge clk_27m)')
s=s[:pos]+'''    reg ext_meta, ext_sync;
    reg ext_pending, ext_selected, ext_running;
    reg [22:0] ext_addr_latched;
    reg [7:0] ext_data_latched;
    reg ext_write_latched;
    wire [22:0] cpu_sdram_addr = ext_selected ? ext_addr_latched : sdram_addr;
    wire cpu_sdram_write = ext_selected ? ext_write_latched : sdram_write;
    wire [7:0] cpu_sdram_din = ext_selected ? ext_data_latched : mapper_din;
    // Payload is stable before the synchronized request and until acknowledgement.
    // Select only between slots; never change a row/column halfway through a slot.
    always @(posedge clk_108m or negedge bus_reset_n) begin
        if (!bus_reset_n) begin
            ext_meta<=0; ext_sync<=0; ext_pending<=0;
            ext_selected<=0; ext_running<=0; ext_done<=0; ext_dout<=8'hff;
            ext_addr_latched<=0; ext_data_latched<=0; ext_write_latched<=0;
        end else begin
            ext_meta<=ext_req; ext_sync<=ext_meta;
            if (!ext_sync && ext_done) ext_done<=0;
            if (ext_sync && !ext_pending && !ext_selected && !ext_done) begin
                ext_addr_latched<=ext_addr; ext_data_latched<=ext_din;
                ext_write_latched<=ext_write; ext_pending<=1;
            end
            if (ext_pending && ff_sdr_seq==3'b111 && RstSeq[4:3]==2'b11) begin
                ext_pending<=0; ext_selected<=1;
            end
            if (ext_selected && !ext_running && ff_sdr_seq==3'b000 &&
                !video_dlclk && SdrSta[2] && RstSeq[4:3]==2'b11)
                ext_running<=1;
            if (ext_running && ff_sdr_seq==3'b111) begin
                ext_dout<=RamDbi; ext_done<=1;
                ext_running<=0; ext_selected<=0;
            end
        end
    end

'''+s[pos:]
# Legacy address staging remains intact; the final mux alone selects extension.
start=s.index('    reg [2:0] ff_sdr_seq;')
a,b=s[:start],s[start:]
b=b.replace('sdram_write;', 'cpu_sdram_write;')
b=b.replace('sdram_addr[', 'cpu_sdram_addr[')
b=b.replace('{ mapper_din, mapper_din, mapper_din, mapper_din }',
            '{ cpu_sdram_din, cpu_sdram_din, cpu_sdram_din, cpu_sdram_din }')
# Read the bidirectional pad net, not the Z-valued output-enable register.
b=b.replace('RamDbi <= SdrDat[','RamDbi <= IO_sdram_dq[')
b=b.replace('vram_dout <= { SdrDat[15:8], SdrDat[7:0] };',
            'vram_dout <= { IO_sdram_dq[15:8], IO_sdram_dq[7:0] };')
b=b.replace('ff_mem_seq <= { ff_mem_seq[0], (~ ff_mem_seq[1]) } ;',
            "if (!bus_reset_n) ff_mem_seq<=0;\n        else ff_mem_seq <= { ff_mem_seq[0], (~ ff_mem_seq[1]) } ;")
b=b.replace("if( ff_sdr_seq == 3'b111 ) begin", "if (!bus_reset_n) SdrSta<=0;\n        else if( ff_sdr_seq == 3'b111 ) begin",1)
b=b.replace('        case (ff_sdr_seq)\n            3\'b000: begin\n                if( video_dhclk',
            "        if (!bus_reset_n) ff_sdr_seq<=0;\n        else case (ff_sdr_seq)\n            3'b000: begin\n                if( video_dhclk",1)
(r/'fpga/src/memory_ez80.v').write_text(a+b)
print('Generated memory_ctrl_ez80; original memory.v unchanged')
