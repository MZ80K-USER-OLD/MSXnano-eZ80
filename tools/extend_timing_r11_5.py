from pathlib import Path
r=Path(__file__).resolve().parent.parent
p=r/'fpga/G80A_eZ80/g80a_ez80.vhd';s=p.read_text()
s=s.replace('    signal Request_Extended : std_logic;', '    signal Request_Extended : std_logic;\n    signal Request_Vector, Vector_Read_Request : std_logic;',1)
s=s.replace("        Write='0' and IORQ='0' and IntCycle_n='1' and RFSH_n_i='1' else '0';", "        IORQ='0' and IntCycle_n='1' and RFSH_n_i='1' else '0';\n    -- R11.5: qualify vector reads only after capturing the request.\n    -- No combinational Write decode enters either address register.\n    Vector_Read_Request <= Request_Vector and not Request_Write;",1)
s=s.replace("           Request_Address when BUSAK_n_i='1' else (others=>'Z');", "           x\"0F\" & Request_Address(15 downto 0) when Vector_Read_Request='1' and BUSAK_n_i='1' else\n           Request_Address when BUSAK_n_i='1' else (others=>'Z');",1)
s=s.replace("             Request_MSX_Address when BUSAK_n_i='1' else (others=>'Z');", "             x\"0000\" when Vector_Read_Request='1' and BUSAK_n_i='1' else\n             Request_MSX_Address when BUSAK_n_i='1' else (others=>'Z');",1)
s=s.replace("else Request_Extended;","else Request_Extended or Vector_Read_Request;",1)
s=s.replace("Request_MSX_Address <= (others=>'0'); Request_Extended <= '0';", "Request_MSX_Address <= (others=>'0'); Request_Extended <= '0'; Request_Vector <= '0';",1)
s=s.replace('                    Request_Address <= Bank_i & A_i;', '                    Request_Address <= Bank_i & A_i; Request_Vector <= Vector_Window;',1)
s=s.replace('''                    elsif Vector_Window='1' then
                        Request_Address <= x"0F" & A_i;
                        Request_MSX_Address <= (others=>'0'); Request_Extended <= '1';
''','',1)
# The removed elsif leaves the if's existing end if in place.
p.write_text(s)
p=r/'fpga/src/memory_ez80.v';s=p.read_text();s=s.replace('    reg ext_meta, ext_sync;','    reg ext_req_sample;\n    reg ext_meta, ext_sync;',1).replace('ext_meta<=ext_req; ext_sync<=ext_meta;','ext_meta<=ext_req_sample; ext_sync<=ext_meta;',1)
s=s.replace('''            ext_addr_sample<=0; ext_data_sample<=0; ext_write_sample<=0;''','''            ext_req_sample<=0;
            ext_addr_sample<=0; ext_data_sample<=0; ext_write_sample<=0;''',1)
s=s.replace('''            ext_addr_sample<=ext_addr; ext_data_sample<=ext_din;''','''            ext_req_sample<=ext_req;
            ext_addr_sample<=ext_addr; ext_data_sample<=ext_din;''',1);p.write_text(s)
