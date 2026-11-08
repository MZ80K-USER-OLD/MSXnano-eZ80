from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();s=s.replace('end T80_eZ80;', '''    -- GOWIN SUG550: avoid a clocked BSRAM ROM on the CPU control path.
    attribute syn_romstyle : string;
    attribute syn_romstyle of T80_eZ80 : entity is "logic";
end T80_eZ80;''',1)
s=s.replace('    signal Wide_Stack, Wide_IncDec : std_logic;', '''    signal Wide_Stack, Wide_IncDec : std_logic;
    signal Opcode_Class : std_logic_vector(5 downto 0);
    function Classify_Opcode(op : std_logic_vector(7 downto 0)) return std_logic_vector is
        variable c : std_logic_vector(5 downto 0) := (others=>'0');
    begin
        if op=x"E3" then c(0):='1';end if;
        if op(7 downto 6)="11" and (op(3 downto 0)="0101" or op(3 downto 0)="0001") then c(1):='1';end if;
        if op(7 downto 6)="00" and (op(3 downto 0)="0011" or op(3 downto 0)="1011") then c(2):='1';end if;
        if op=x"32" or op=x"3A" then c(3):='1';end if;
        if op=x"22" or op=x"2A" then c(4):='1';end if;
        if op(7 downto 6)="01" and op(2 downto 0)="011" then c(5):='1';end if;
        return c;
    end function;''',1)
s=s.replace('IR <= "00000000";', 'IR <= "00000000"; Opcode_Class<=Classify_Opcode(x"00");')
s=s.replace('IR <= "11111111";', 'IR <= "11111111"; Opcode_Class<=Classify_Opcode(x"FF");')
s=s.replace('IR <= DInst;', 'IR <= DInst; Opcode_Class<=Classify_Opcode(DInst);')
s=s.replace('IntCycle=\'0\' and NMICycle=\'0\' and IR(7 downto 6)="11" and\n        (IR(3 downto 0)="0101" or IR(3 downto 0)="0001")', "IntCycle='0' and NMICycle='0' and Opcode_Class(1)='1'")
s=s.replace('IntCycle=\'0\' and NMICycle=\'0\' and IR(7 downto 6)="00" and\n        (IR(3 downto 0)="0011" or IR(3 downto 0)="1011")', "IntCycle='0' and NMICycle='0' and Opcode_Class(2)='1'")
s=s.replace('((ISet="00" and (IR=x"22" or IR=x"2A")) or (ISet="10" and IR(7 downto 6)="01" and IR(2 downto 0)="011"))', '((ISet="00" and Opcode_Class(4)=\'1\') or (ISet="10" and Opcode_Class(5)=\'1\'))',1)
s=s.replace('(IR=x"32" or IR=x"3A") and IntCycle=', "Opcode_Class(3)='1' and IntCycle=",1)
s=s.replace('ISet="00" and IR=x"E3" and IntCycle=', 'ISet="00" and Opcode_Class(0)=\'1\' and IntCycle=',1)
p.write_text(s)
p=r/'fpga/src/memory_ez80.v';s=p.read_text();s=s.replace('reg ext_meta, ext_sync;', '''reg ext_meta, ext_sync;
    // Separate the synchronizer from the one-shot payload capture enable.
    reg ext_capture_armed;''',1)
s=s.replace('ext_meta<=0; ext_sync<=0; ext_pending<=0;', 'ext_meta<=0; ext_sync<=0; ext_capture_armed<=0; ext_pending<=0;',1)
s=s.replace('            if (ext_sync && !ext_pending && !ext_selected && !ext_done) begin', '''            ext_capture_armed <= ext_sync && !ext_pending && !ext_selected && !ext_done && !ext_capture_armed;
            if (ext_capture_armed) begin''',1)
p.write_text(s)
p=r/'fpga/tang20k.sdc';s=p.read_text();s=s.replace('-name clock_27m -source [get_pins {clk_main/rpll_inst/CLKOUT}] -master_clock clock_108m -divide_by 4', '-name clock_27m -source [get_ports {ex_clk_27m}] -master_clock clock_input -divide_by 1')
s=s.replace('-name clock_54m -source [get_pins {clk_main/rpll_inst/CLKOUT}] -master_clock clock_108m -divide_by 2', '-name clock_54m -source [get_ports {ex_clk_27m}] -master_clock clock_input -multiply_by 2')
s='// R11.2: use the common external source for PLL/CLKDIV clock definitions.\n// No source/network latency constants and no new timing exceptions.\n'+s;p.write_text(s)
print('Applied R11.2 opcode class FFs, CPU ROM mapping, registered SDRAM capture, common clock root')
