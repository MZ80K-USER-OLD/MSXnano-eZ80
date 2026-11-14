from pathlib import Path
r=Path(__file__).resolve().parent.parent
s=(r/'fpga/top_ez80.v').read_text()
assert '.A24' not in s
s=s.replace('parameter SD_SLOT = 3 // 3', '''parameter SD_SLOT = 3, // 3
    // v33 compatibility default. Set 1 for the DI-only development profile.
    parameter EZ80_EXTENDED = 0''',1)
s=s.replace('    wire bus_mreq_n;', '''    wire bus_mreq_n;
    wire cpu_mreq_n;
    wire [15:0] cpu_addr16;
    wire [23:0] cpu_addr24;
    wire ext_cycle, ext_wait_n;
    wire [7:0] ext_cpu_din;
    wire ext_ram_req, ext_ram_write, ext_ram_done;
    wire [22:0] ext_ram_addr;
    wire [7:0] ext_ram_din, ext_ram_dout;
    ez80_memory_bridge memory_bridge (
        .clk(clk_54m), .reset_n(bus_reset_n & reset3_n),
        .cpu_addr(cpu_addr24), .cpu_mreq_n(cpu_mreq_n),
        .cpu_iorq_n(bus_iorq_n), .cpu_rfsh_n(bus_rfsh_n),
        .cpu_rd_n(bus_rd_n), .cpu_wr_n(bus_wr_n), .cpu_dout(cpu_dout),
        .msx_mreq_n(bus_mreq_n), .msx_addr(bus_addr),
        .extended_cycle(ext_cycle), .wait_n(ext_wait_n), .cpu_din(ext_cpu_din),
        .ram_req(ext_ram_req), .ram_write(ext_ram_write), .ram_addr(ext_ram_addr),
        .ram_din(ext_ram_din), .ram_done(ext_ram_done), .ram_dout(ext_ram_dout)
    );''',1)
s=s.replace('        cpu_din <= \n', '        cpu_din <= \n                ext_cycle ? ext_cpu_din :\n',1)
start=s.index('    G80A_eZ80 #(')
end=s.index('`endif\n\n    wire mapper_write;',start) if '`endif\n\n    wire mapper_write;' in s[start:] else s.index('    wire mapper_write;',start)
# Modify only the two CPU instances; shared MSX decoders remain untouched.
a,b,c=s[:start],s[start:end],s[end:]
b=b.replace('.Mode    (0),', '''.FETCH24 (EZ80_EXTENDED),
        .ENABLE_MIXED (EZ80_EXTENDED),
        .ENABLE_SUFFIX_V2 (EZ80_EXTENDED),
        .ENABLE_EZ80_ISA (EZ80_EXTENDED),
        .RESET_ADL (0),
        .Mode    (0),''',1)
b=b.replace('(bus_wait_n & flash_wait_n)', '(bus_wait_n & flash_wait_n & ext_wait_n)')
b=b.replace('(bus_wait_n),','(bus_wait_n & ext_wait_n),')
b=b.replace('.MREQ_n    (bus_mreq_n)', '.MREQ_n    (cpu_mreq_n)')
b=b.replace('.A         (bus_addr)', '.A         (cpu_addr16)')
b=b.replace('.A         (cpu_addr16),', '.A         (cpu_addr16),\n        .A24       (cpu_addr24),',1)
b=b.replace('`else\n    G80a', "`else\n    assign cpu_addr24 = {8'h00,cpu_addr16};\n    G80a",1)
s=a+b+c
s=s.replace('memory_ctrl mem1 (','''memory_ctrl_ez80 mem1 (
    .ext_req(ext_ram_req), .ext_write(ext_ram_write), .ext_addr(ext_ram_addr),
    .ext_din(ext_ram_din), .ext_done(ext_ram_done), .ext_dout(ext_ram_dout),''',1)
(r/'fpga/top_ez80.v').write_text(s)
p=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj'
s=p.read_text().replace('<File path="../src/memory.v" type="file.verilog" enable="1"/>',
'''<File path="../src/memory_ez80.v" type="file.verilog" enable="1"/>
        <File path="../src/ez80_memory_bridge.v" type="file.verilog" enable="1"/>''')
p.write_text(s)
print('Connected A24/MSX isolation/WAIT, added controller and bridge to eZ80 GPRJ')
