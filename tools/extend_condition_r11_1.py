from pathlib import Path
import re
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd';s=p.read_text();fun=s[s.index('        function is_cc_true('):s.index('\nbegin\n')].strip()
s=s.replace('                Flow_Cond : out std_logic;', '                Flow_Cond : out std_logic;\n                Branch_Condition : in std_logic;')
s=s.replace('Has_Width, Interrupt_Mode)', 'Has_Width, Interrupt_Mode, Branch_Condition)')
s=re.sub(r'if is_cc_true\(F,\s*to_bitvector\(IR\(5 downto 3\)\)\) then Flow_Cond<=\'1\';else Flow_Cond<=\'0\';end if;', 'Flow_Cond <= Branch_Condition;',s)
s=re.sub(r'is_cc_true\(F,\s*to_bitvector\(IR\(5 downto 3\)\)\)', "Branch_Condition='1'",s)
p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_pack_ez80.vhd';s=p.read_text();needle='Flow_Cond : out std_logic;';assert needle in s;s=s.replace(needle,needle+'\n                Branch_Condition : in std_logic;');p.write_text(s)
p=r/'fpga/G80A_eZ80/t80_ez80.vhd';s=p.read_text();s=s.replace('    signal Decode_Flags :', '    signal Branch_Condition : std_logic;\n    signal Decode_Flags :',1)
s=s.replace('    function PC_Width', '    '+fun.replace('is_cc_true','decode_branch')+'\n    function PC_Width',1)
s=s.replace("if RESET_n='0' then Decode_Flags <= (others=>'1');", "if RESET_n='0' then Decode_Flags <= (others=>'1');Branch_Condition<='0';")
s=s.replace('                Decode_Flags <= F;', "                Decode_Flags <= F;\n                if decode_branch(F,to_bitvector(DInst(5 downto 3))) then Branch_Condition<='1';else Branch_Condition<='0';end if;")
s=s.replace('Flow_Cond=>Flow_Cond, Interrupt_Mode=>IStatus,','Flow_Cond=>Flow_Cond, Branch_Condition=>Branch_Condition, Interrupt_Mode=>IStatus,')
p.write_text(s)
print('Applied instruction boundary branch condition register')
