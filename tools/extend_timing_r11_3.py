from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/g80a_ez80.vhd';s=p.read_text()
s=s.replace('        Data_Reverse: out std_logic\n','''        Data_Reverse: out std_logic;
        A_MSX : out std_logic_vector(15 downto 0);
        Extended_Window : out std_logic
''',1)
s=s.replace('    signal Request_Write, Request_IO : std_logic;','''    signal Request_Write, Request_IO : std_logic;
    signal Request_MSX_Address : std_logic_vector(15 downto 0);
    signal Request_Extended : std_logic;''',1)
s=s.replace('    DO <= Request_Data;','''    -- R11.3: isolate the MSX address at the same edge as the full request.
    -- Refresh remains bank zero; ordinary addresses never use a live bank mux.
    A_MSX <= A_i when RFSH_n_i='0' and BUSAK_n_i='1' else
             Request_MSX_Address when BUSAK_n_i='1' else (others=>'Z');
    Extended_Window <= '0' when RFSH_n_i='0' else Request_Extended;
    DO <= Request_Data;''',1)
s=s.replace("            Request_Write <= '0'; Request_IO <= '0';", "            Request_Write <= '0'; Request_IO <= '0';\n            Request_MSX_Address <= (others=>'0'); Request_Extended <= '0';",1)
s=s.replace('                    Request_Address <= Bank_i & A_i;','''                    Request_Address <= Bank_i & A_i;
                    Request_MSX_Address <= (others=>'0'); Request_Extended <= '1';
                    if Bank_i=x"00" then
                        Request_MSX_Address <= A_i; Request_Extended <= '0';
                    end if;''',1)
s=s.replace('                        Request_Address <= x"00" & A_i;','''                        Request_Address <= x"00" & A_i;
                        Request_MSX_Address <= A_i; Request_Extended <= '0';''',1)
s=s.replace('                        Request_Address <= x"0F" & A_i;','''                        Request_Address <= x"0F" & A_i;
                        Request_MSX_Address <= (others=>'0'); Request_Extended <= '1';''',1);p.write_text(s)
p=r/'fpga/src/ez80_memory_bridge.v';s=p.read_text().replace('parameter REQUEST_BANK_QUALIFIED = 0','parameter REQUEST_BANK_QUALIFIED = 0,\n    parameter PREDECODED_MSX = 0',1)
s=s.replace('    input wire [7:0] ram_dout\n','''    input wire [7:0] ram_dout,
    // Only enable PREDECODED_MSX with the R11.3 wrapper's registered outputs.
    input wire [15:0] cpu_msx_addr,
    input wire cpu_extended_window
''',1)
s=s.replace("    wire extended_window = bank != 8'h00 &&", "    wire extended_window = PREDECODED_MSX ? cpu_extended_window : bank != 8'h00 &&",1)
s=s.replace("    assign msx_addr = extended_window ? 16'h0000 : cpu_addr[15:0];","    assign msx_addr = PREDECODED_MSX ? cpu_msx_addr : extended_window ? 16'h0000 : cpu_addr[15:0];",1);p.write_text(s)
p=r/'fpga/top_ez80.v';s=p.read_text().replace('    wire [23:0] cpu_addr24;','''    wire [23:0] cpu_addr24;
    wire [15:0] cpu_msx_addr;
    wire cpu_extended_window;''',1)
s=s.replace('.REQUEST_BANK_QUALIFIED(1)','.REQUEST_BANK_QUALIFIED(1), .PREDECODED_MSX(1)',1)
s=s.replace('        .cpu_addr(cpu_addr24), .cpu_mreq_n(cpu_mreq_n),','''        .cpu_addr(cpu_addr24), .cpu_mreq_n(cpu_mreq_n),
        .cpu_msx_addr(cpu_msx_addr), .cpu_extended_window(cpu_extended_window),''',1)
s=s.replace('        .A24       (cpu_addr24),','''        .A24       (cpu_addr24),
        .A_MSX     (cpu_msx_addr), .Extended_Window(cpu_extended_window),''',1)
# The non-eZ80 build keeps the legacy bridge profile; provide defined unused inputs.
s=s.replace('    assign cpu_addr24 = {8\'h00,cpu_addr16};',"    assign cpu_addr24 = {8'h00,cpu_addr16};\n    assign cpu_msx_addr = cpu_addr16;\n    assign cpu_extended_window = 1'b0;",1);p.write_text(s)
p=r/'fpga/src/memory_ez80.v';s=p.read_text()
s=s.replace('            ext_addr_latched<=0; ext_data_latched<=0; ext_write_latched<=0;\n','',1)
s=s.replace('''                ext_addr_latched<=ext_addr; ext_data_latched<=ext_din;
                ext_write_latched<=ext_write; ext_pending<=1;''','''                // Payload was captured on the intervening falling edge.
                ext_pending<=1;''',1)
needle='    always @ (posedge clk_27m) begin'
assert needle in s
s=s.replace(needle,'''    // R11.3: the sender launches on clk_54m rising edges. Capture held
    // payload on clk_108m falling edges, after the synchronized arm.
    // The following rising edge publishes pending; scheduling remains unchanged.
    always @(negedge clk_108m or negedge bus_reset_n) begin
        if (!bus_reset_n) begin
            ext_addr_latched<=0; ext_data_latched<=0; ext_write_latched<=0;
        end else if (ext_capture_armed) begin
            ext_addr_latched<=ext_addr; ext_data_latched<=ext_din;
            ext_write_latched<=ext_write;
        end
    end

'''+needle,1);p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text().replace('Opcode_Class : std_logic_vector(5 downto 0)','Opcode_Class : std_logic_vector(15 downto 0)',1).replace("variable c : std_logic_vector(5 downto 0)","variable c : std_logic_vector(15 downto 0)",1)
s=s.replace('        return c;','''        if op(7 downto 6)="00" and op(3 downto 0)="1001" then c(6):='1';end if;
        if op(7 downto 6)="01" and op(2 downto 0)="010" then c(7):='1';end if;
        if op(7 downto 5)="101" and op(2 downto 1)="00" then c(8):='1';end if;
        if op(7 downto 6)="01" and op(3 downto 0)="1100" then c(9):='1';end if;
        if op=x"02" or op=x"03" or op=x"12" or op=x"13" or op=x"22" or op=x"23" or
           op=x"32" or op=x"33" or op=x"54" or op=x"55" or op=x"65" or op=x"66" then c(10):='1';end if;
        if op=x"65" or op=x"66" then c(11):='1';end if;
        if op=x"C3" or (op(7 downto 6)="11" and op(2 downto 0)="010") then c(12):='1';end if;
        if op=x"CD" or op=x"C9" or (op(7 downto 6)="11" and
           (op(2 downto 0)="100" or op(2 downto 0)="000" or op(2 downto 0)="111")) then c(13):='1';end if;
        if op=x"45" or op=x"4D" then c(14):='1';end if;
        if op=x"D7" then c(15):='1';end if;
        return c;''',1)
repls=[('((ISet="00" and IR(7 downto 6)="00" and IR(3 downto 0)="1001") or\n         (ISet="10" and IR(7 downto 6)="01" and IR(2 downto 0)="010"))','((ISet="00" and Opcode_Class(6)=\'1\') or\n         (ISet="10" and Opcode_Class(7)=\'1\'))'),
('ISet="10" and IR(7 downto 5)="101" and\n        IR(2 downto 1)="00"','ISet="10" and Opcode_Class(8)=\'1\''),
('IR(7 downto 6)="01" and IR(3 downto 0)="1100" and IntCycle','Opcode_Class(9)=\'1\' and IntCycle'),
('(IR=x"02" or IR=x"03" or IR=x"12" or IR=x"13" or IR=x"22" or IR=x"23" or\n         IR=x"32" or IR=x"33" or IR=x"54" or IR=x"55" or IR=x"65" or IR=x"66")','Opcode_Class(10)=\'1\''),
('PEA_Active<=EA_Active when IR=x"65" or IR=x"66"','PEA_Active<=EA_Active when Opcode_Class(11)=\'1\''),
('(IR=x"C3" or (IR(7 downto 6)="11" and IR(2 downto 0)="010"))','Opcode_Class(12)=\'1\''),
('(IR=x"45" or IR=x"4D")','Opcode_Class(14)=\'1\''),
('ISet="10" and IR=x"D7" and MCycle','ISet="10" and Opcode_Class(15)=\'1\' and MCycle'),
('(IR=x"CD" or IR=x"C9" or (IR(7 downto 6)="11" and\n        (IR(2 downto 0)="100" or IR(2 downto 0)="000" or IR(2 downto 0)="111")))','Opcode_Class(13)=\'1\'')]
for a,b in repls:
 assert a in s,a
 s=s.replace(a,b,1)
p.write_text(s)
