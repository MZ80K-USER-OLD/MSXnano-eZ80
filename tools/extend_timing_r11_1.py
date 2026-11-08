from pathlib import Path
import re
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();head,body=s.split('architecture rtl of T80_eZ80 is',1)
# Keep entity ports unchanged; read and write internal registers, never out ports.
for old,new in [('A_BANK','Address_Bank_Reg'),('A','Address_Reg'),('DO','Data_Out_Reg'),('Write','Write_Decode')]:
 body=re.sub(r'\b'+old+r'\b',new,body,flags=re.I)
body=body.replace('    constant aNone', '''    signal Address_Reg : std_logic_vector(15 downto 0);
    signal Address_Bank_Reg, Data_Out_Reg : std_logic_vector(7 downto 0);
    signal Write_Decode : std_logic;
    signal Decode_Flags : std_logic_vector(7 downto 0);
    constant aNone''',1)
# Named associations are formal names, not out-port reads.
body=body.replace('Write_Decode => Write_Decode','Write => Write_Decode')
body=body.replace('F => F,','F => Decode_Flags,',1)
mark='\nbegin\n'
i=body.index(mark);body=body[:i]+body[i:].replace(mark,'''begin
    A <= Address_Reg;
    A_BANK <= Address_Bank_Reg;
    DO <= Data_Out_Reg;
    Write <= Write_Decode;
    -- The previous instruction's delayed flag write completes at fetch T1.
    -- Capture at accepted fetch T2, alongside IR, and hold for the instruction.
    process(RESET_n, CLK_n)
    begin
        if RESET_n='0' then Decode_Flags <= (others=>'1');
        elsif rising_edge(CLK_n) then
            if ClkEn='1' and MCycle="001" and TState=2 and WAIT_n='1' then
                Decode_Flags <= F;
            end if;
        end if;
    end process;
''',1)
p.write_text(head+'architecture rtl of T80_eZ80 is'+body)
p=r/'fpga/G80A_eZ80/g80a_ez80.vhd';s=p.read_text();s=s.replace('    --signal DO           : std_logic_vector(7 downto 0);','''    signal Core_DO, Request_Data : std_logic_vector(7 downto 0);
    signal Request_Address : std_logic_vector(23 downto 0);
    signal Request_Write, Request_IO : std_logic;''')
s=s.replace('DO => DO,','DO => Core_DO,')
s=s.replace('if DO=', 'if Core_DO=').replace('or DO=', 'or Core_DO=').replace('elsif DO(', 'elsif Core_DO(').replace('if DO(7 downto 4)=','if Core_DO(7 downto 4)=').replace('Diag_Select<=DO','Diag_Select<=Core_DO').replace('case DO is','case Core_DO is')
s=s.replace('    A24 <= x"0F" & A_i when Vector_Window=\'1\' and BUSAK_n_i=\'1\' else\n           Bank_i & A_i when BUSAK_n_i=\'1\' else (others=>\'Z\');', '''    -- Only the refresh phase uses the core's refresh address directly.
    -- All ordinary requests retain their T1 address through WAIT and bus release.
    A24 <= x"00" & A_i when RFSH_n_i='0' and BUSAK_n_i='1' else
           Request_Address when BUSAK_n_i='1' else (others=>'Z');
    DO <= Request_Data;
    process(RESET_n, CLK_n)
    begin
        if RESET_n='0' then
            Request_Address <= (others=>'0'); Request_Data <= (others=>'0');
            Request_Write <= '0'; Request_IO <= '0';
        elsif falling_edge(CLK_n) then
            if clk_falling='1' then
                if TState="001" then
                    Request_Address <= Bank_i & A_i;
                    if IORQ='1' or (IntCycle_n='0' and MCycle="001") then
                        Request_Address <= x"00" & A_i;
                    elsif Vector_Window='1' then
                        Request_Address <= x"0F" & A_i;
                    end if;
                    Request_Write <= Write; Request_IO <= IORQ;
                end if;
                -- Core data can be refreshed during an automatic T1 wait.
                -- It is final before the memory write strobe at T2.
                if TState="001" or TState="010" then Request_Data <= Core_DO; end if;
            end if;
        end if;
    end process;''')
s=s.replace('Data_Reverse <= Write;','Data_Reverse <= Request_Write;')
s=s.replace('if A_i=x"E7E7" and IORQ=\'1\' and Write=\'0\' and IntCycle_n=\'1\' then DI_Reg', 'if Request_Address(15 downto 0)=x"E7E7" and Request_IO=\'1\' and Request_Write=\'0\' and IntCycle_n=\'1\' then DI_Reg')
s=s.replace('WR_n_i <= not Write;','WR_n_i <= not Request_Write;')
p.write_text(s)
p=r/'fpga/src/ez80_memory_bridge.v';s=p.read_text().replace('module ez80_memory_bridge (','''module ez80_memory_bridge #(
    // Enable only with the R11.1 wrapper, which forces bank zero for I/O/IACK/refresh.
    parameter REQUEST_BANK_QUALIFIED = 0
) (''');s=s.replace("wire extended_window = bank != 8'h00 && cpu_iorq_n && cpu_rfsh_n;", "wire extended_window = bank != 8'h00 &&\n        (REQUEST_BANK_QUALIFIED || (cpu_iorq_n && cpu_rfsh_n));")
p.write_text(s)
p=r/'fpga/top_ez80.v';s=p.read_text().replace('ez80_memory_bridge memory_bridge (','''ez80_memory_bridge #(
`ifdef MSXNANO_USE_EZ80
        .REQUEST_BANK_QUALIFIED(1)
`else
        .REQUEST_BANK_QUALIFIED(0)
`endif
    ) memory_bridge (''');p.write_text(s)
# Preserve all existing exceptions, but remove the false audio root clock.
# Fractional-divider pulses are 612/614 source clocks apart; model the shortest.
p=r/'fpga/tang20k.sdc';s=p.read_text();s=s.replace('create_clock -name clock_audio -period 277.778 -waveform {0 138.889} [get_nets {vdp4/clk_audio}] -add', '''// R11.1: shortest 44.1 kHz fractional-divider period is 612 parent clocks.
// 27 MHz / 44.1 kHz is non-integral; this is a conservative minimum interval.
create_generated_clock -name clock_audio -source [get_nets {clk_27m}] -master_clock clock_27m -divide_by 612 [get_nets {vdp4/clk_audio}] -add''')
p.write_text(s)
print('Applied R11.1 request snapshots, instruction flags and audio clock model')

# Build the actual input -> PLL -> CLKDIV clock tree. VideoDH/DL are data
# phase signals sampled by memory_ctrl_ez80, not clock pins.
p=r/'fpga/tang20k.sdc';s=p.read_text();lines=s.splitlines();out=[]
for line in lines:
    if line.startswith('create_clock ') or line.startswith('create_generated_clock '):
        continue
    out.append(line)
clocks='// R11.1 clock tree: no new false paths or multicycle exceptions.\ncreate_clock -name clock_input -period 37.037 [get_ports {ex_clk_27m}]\ncreate_generated_clock -name clock_108m -source [get_ports {ex_clk_27m}] -master_clock clock_input -multiply_by 4 [get_pins {clk_main/rpll_inst/CLKOUT}]\ncreate_generated_clock -name clock_27m -source [get_pins {clk_main/rpll_inst/CLKOUT}] -master_clock clock_108m -divide_by 4 [get_nets {clk_27m}]\ncreate_generated_clock -name clock_54m -source [get_pins {clk_main/rpll_inst/CLKOUT}] -master_clock clock_108m -divide_by 2 [get_nets {clk_54m}]\n// Fractional 44.1 kHz divider: minimum interval 612 parent periods.\ncreate_generated_clock -name clock_audio -source [get_nets {clk_27m}] -master_clock clock_27m -divide_by 612 [get_nets {vdp4/clk_audio}]\n// VideoDHClk and VideoDLClk remain timing data from their actual 27 MHz FFs.\n'
p.write_text(clocks+'\n'+'\n'.join(out)+'\n')
p=r/'fpga/top_ez80.v';s=p.read_text().replace('    always_latch begin\n        if (~bus_reset_n) begin', '    // Configuration follows updates while reset is held; retain it after release.\n    // This uses the system clock rather than a transparent reset-controlled latch.\n    always @(posedge clk_27m) begin\n        if (~bus_reset_n) begin',1);p.write_text(s)

p=r/'fpga/tn_vdp_v3_v9958/src/clockdiv.v';s=p.read_text().replace('logic clkd;', 'logic clkd = 0;').replace('$pow(2,PRECISION_BITS)', '$pow(2.0,PRECISION_BITS)');p.write_text(s)

# Power-up must work even if PLL lock releases reset before a 27 MHz edge.
p=r/'fpga/top_ez80.v';s=p.read_text()
for name,value in [('config_enable_mapper3', "1'b1"),('config_enable_mapper12', "1'b0"),('config_enable_sdcard', "1'b1")]:
    old='reg '+name+';';assert s.count(old)==1,name
    s=s.replace(old,'reg '+name+' = '+value+';')
p.write_text(s)
