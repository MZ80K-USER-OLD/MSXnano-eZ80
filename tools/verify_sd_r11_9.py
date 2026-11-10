from pathlib import Path
import re,os,subprocess,json,concurrent.futures,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_sd_r11_9';w.mkdir(exist_ok=True)
# Extract the actual register control RTL; do not recreate the DUT logic in the test.
old=(r/'doc/r11_7_sd_baseline/top_ez80.v.txt').read_text();new=(r/'fpga/top_ez80.v').read_text()
inputs={'clk_27m':'','bus_reset_n':'','config_enable_sdcard':'','pri_slot_num':'[3:0]','exp_slotx_num':'[3:0]','bus_addr':'[15:0]','bus_wr_n':'','bus_rd_n':'','bus_iorq_n':'','bus_m1_n':'','bus_mreq_n':'','cpu_dout':'[7:0]','sd_done_w':'','sd_busy_w':'','sd_timeout_error_w':'','sd_crc_error_w':'','sd_c_size_w':'[21:0]','sd_c_size_mult_w':'[2:0]','sd_read_bl_len_w':'[3:0]','sd_card_type_w':'[1:0]','sd_mid_w':'[7:0]','sd_oid_w':'[15:0]','sd_pnm_w':'[39:0]','sd_psn_w':'[31:0]'}
outputs={'ff_sd_en':'','ff_sd_rstart':'','ff_sd_wstart':'','ff_sd_init':'','ff_sd_sector':'[31:0]','sd_cd_w':'[7:0]','sd_cs_w':'','sd_busreq_w':''}
for label,src in [('reference',old),('candidate',new)]:
 a=src.index('    localparam int SDC_SDATA');b=src.index('    wire [8:0] sram_addr_w;',a);params=src[a:b]
 a=src.index('    always @(posedge clk_27m or negedge bus_reset_n) begin\n        if (~bus_reset_n) begin\n            ff_sd_en');b=src.index('\n`else',a);body=src[a:b]
 ss=f'module sd_{label}('+','.join(list(inputs)+list(outputs))+');\nlocalparam SD_SLOT=3;\n'
 for n,t in inputs.items():ss+=f'input {t} {n};\n'
 for n,t in outputs.items():ss+=f'output {t} {n};\n'
 ss+='reg ff_sd_en=0;reg ff_sd_rstart,ff_sd_wstart,ff_sd_init;reg[31:0]ff_sd_sector;\n'+params+body+'\nendmodule\n'
 (w/(label+'.sv')).write_text(ss)
# Fixed register-device responses, including all reserved offsets.
values={0:1,2:0x81,7:0xa5,8:0x23,9:0x31,10:5,11:9,12:3,13:0x42,14:0x7e,15:0xca,16:0x11,17:0x22,18:0x33,19:0x44,20:0x55,21:0xef,22:0xcd,23:0xab,24:0x89}
mem=bytearray(65536);pc=0x100;fixups=[]
def emit(*bs):
 global pc
 mem[pc:pc+len(bs)]=bytes(bs);pc+=len(bs)
def ldwrite(addr,val):emit(0x3e,val,0x32,addr&255,addr>>8)
def compare(addr,val):
 emit(0x3a,addr&255,addr>>8,0xfe,val,0xc2);fixups.append(pc);emit(0,0)
emit(0xf3,0x31,0,0xf0);ldwrite(0x7e00,1)
for i,v in enumerate([0x12,0x34,0x56,0x78]):ldwrite(0x7e03+i,v)
ldwrite(0x7e01,0x83)
for i in range(256):compare(0x7e00+i,values.get(i,255))
emit(0x21,0,0x7e,0x11,0,0x80,0x01,0,1,0xed,0xb0)
for i in range(256):compare(0x8000+i,values.get(i,255))
ldwrite(0xff0,0xa5);emit(0x76);fail=pc;ldwrite(0xff0,0xee);emit(0x76)
for at in fixups:mem[at:at+2]=fail.to_bytes(2,'little')
(w/'program.hex').write_text(''.join(f'{b:02x}\n' for b in mem))
# Testbench instantiates the real converted G80A and the real bridge, comparing
# old/new device data at the actual CPU wrapper T3 capture edge.
ss='''`timescale 1ns/1ps
module tb_sd_r11_9;
parameter CPU_DIV=16,PHASE=0,STRESS=0,FAULT=0;
reg clk=0,clk27=0,cpu_reset=0,sd_reset=0;always #10 clk=~clk;
initial begin #(PHASE);forever #20 clk27=~clk27;end
integer div=0,ticks=0,reads=0,direct_reads=0,isolated=0,waits=0,pauses=0;
reg run_enable=1;
always @(posedge clk)begin
 ticks<=ticks+1;
 if(!cpu_reset)begin div<=0;run_enable<=1;end
 else begin
  if(div==CPU_DIV-1)begin div<=0;run_enable<=!STRESS||ticks%251<180;end else div<=div+1;
  if(STRESS&&!run_enable)pauses<=pauses+1;
 end
end
wire ce=div==0&&run_enable,cf=div==CPU_DIV/2&&run_enable;
wire wait_n=!STRESS||ticks%71<45;
wire[23:0]ca;wire[15:0]cmsx;wire cext,cmr,cio,crf,crd,cwr,cm1,halt_n;wire[7:0]co;
reg[7:0] cpu_din=255,reference_din=255,mem[0:65535];
G80A_eZ80 cpu(.RESET_n(cpu_reset),.CLK_n(clk),.clk_enable(ce),.clk_falling(cf),.WAIT_n(wait_n),.INT_n(1'b1),.NMI_n(1'b1),.BUSRQ_n(1'b1),.DI(cpu_din),.A24(ca),.A_MSX(cmsx),.Extended_Window(cext),.MREQ_n(cmr),.IORQ_n(cio),.RFSH_n(crf),.RD_n(crd),.WR_n(cwr),.DO(co),.M1_n(cm1),.HALT_n(halt_n));
reg manual=1;reg[23:0] manual_addr=0;reg manual_mr=1,manual_rd=1,manual_wr=1;reg[7:0]manual_data=0;
wire[23:0] a=manual?manual_addr:ca;
wire mr=manual?manual_mr:cmr,rd=manual?manual_rd:crd,wr=manual?manual_wr:cwr,io=manual?1'b1:cio,m1=manual?1'b1:cm1;
wire[7:0] dout=manual?manual_data:co;
wire[15:0] ma;wire mm,ext,bridge_wait,ram_req,ram_write;wire[22:0] ram_addr;wire[7:0] ram_data,ext_data;
ez80_memory_bridge #(.REQUEST_BANK_QUALIFIED(1),.PREDECODED_MSX(1)) bridge(.clk(clk),.reset_n(sd_reset),.cpu_addr(a),.cpu_mreq_n(mr),.cpu_iorq_n(io),.cpu_rfsh_n(manual?1'b1:crf),.cpu_rd_n(rd),.cpu_wr_n(wr),.cpu_dout(dout),.cpu_msx_addr(manual?(manual_addr[23:16]!=0?16'h0:manual_addr[15:0]):cmsx),.cpu_extended_window(manual?(manual_addr[23:16]!=0):cext),.msx_addr(ma),.msx_mreq_n(mm),.extended_cycle(ext),.wait_n(bridge_wait),.cpu_din(ext_data),.ram_req(ram_req),.ram_write(ram_write),.ram_addr(ram_addr),.ram_din(ram_data),.ram_done(1'b0),.ram_dout(8'hff));
'''
for lab,entity in [('old','reference'),('new','candidate')]:
 for n,t in outputs.items():ss+=f'wire {t} {lab}_{n};\n'
 args=dict(clk_27m='clk27',bus_reset_n='sd_reset',config_enable_sdcard="1'b1",pri_slot_num="4'b1000",exp_slotx_num="4'b0100",bus_addr='ma',bus_wr_n='wr',bus_rd_n='rd',bus_iorq_n='io',bus_m1_n='m1',bus_mreq_n='mm',cpu_dout='dout',sd_done_w="1'b0",sd_busy_w="1'b1",sd_timeout_error_w="1'b0",sd_crc_error_w="1'b1",sd_c_size_w="22'h3123a5",sd_c_size_mult_w="3'd5",sd_read_bl_len_w="4'd9",sd_card_type_w="2'd3",sd_mid_w="8'h42",sd_oid_w="16'hca7e",sd_pnm_w="40'h5544332211",sd_psn_w="32'h89abcdef")
 args.update({n:f'{lab}_{n}' for n in outputs});ss+=f'sd_{entity} {lab}_sd('+','.join('.'+n+'('+v+')' for n,v in args.items())+');\n'
ss+='''function automatic[7:0] expected(input[7:0]idx);begin case(idx)
'''
for i,v in values.items():ss+=f"8'h{i:02x}:expected=8'h{v:02x};\n"
ss+='''default:expected=255;endcase end endfunction
always @(posedge clk)begin
 if(cpu_reset)begin
  cpu_din<=ext?ext_data:new_sd_busreq_w?new_sd_cd_w:mem[a[15:0]];
  reference_din<=ext?ext_data:old_sd_busreq_w?old_sd_cd_w:mem[a[15:0]];
  if(!mr&&!wr&&mm==0)mem[ma]<=dout;
  if(ce&&cpu.u0.tstate==2&&!cpu.u0.wait_n)waits<=waits+1;
 end
end
always @(posedge clk27)begin #0.01;
 if(sd_reset&&({new_ff_sd_en,new_ff_sd_rstart,new_ff_sd_wstart,new_ff_sd_init,new_ff_sd_sector,new_sd_cs_w,new_sd_busreq_w}!=={old_ff_sd_en,old_ff_sd_rstart,old_ff_sd_wstart,old_ff_sd_init,old_ff_sd_sector,old_sd_cs_w,old_sd_busreq_w}))$fatal(1,"SD write/select state differs");
end
always @(negedge clk)if(cpu_reset&&cf&&cpu.tstate==3&&!mr&&!rd&&a[23:16]==0&&a[15:8]==8'h7e)begin
 if(cpu_din!==reference_din||cpu_din!==expected(a[7:0]))$fatal(1,"CPU SD read mismatch addr=%h expected=%h old=%h new=%h",a,expected(a[7:0]),reference_din,cpu_din);
 reads=reads+1;
end
wire[7:0] truncated_index={4'b0,ma[3:0]};
integer i,b;
initial begin
 $readmemh("verification_sd_r11_9/program.hex",mem);
 if(FAULT==1)force new_sd.sd_read_index=8'h0;
 if(FAULT==2)force new_sd.sd_read_index=truncated_index;
 repeat(5)@(negedge clk27);sd_reset=1;
 @(negedge clk27);manual_addr=24'h007e00;manual_data=1;manual_mr=0;manual_wr=0;
 repeat(4)@(negedge clk27);manual_wr=1;manual_rd=0;
 for(i=0;i<256;i=i+1)begin
  manual_addr=24'h007e00+i;repeat(4)@(negedge clk27);
  if(old_sd_cd_w!==expected(i)||new_sd_cd_w!==expected(i))$fatal(1,"SD read mismatch offset=%h old=%h new=%h expected=%h",i,old_sd_cd_w,new_sd_cd_w,expected(i));
  direct_reads=direct_reads+1;
 end
 manual_rd=1;manual_wr=0;manual_data=0;
 for(b=1;b<256;b=b+1)begin
  manual_addr=(b<<16)|16'h7e00;repeat(3)@(negedge clk27);
  if(ma!==0||mm!==1||new_sd_cs_w!==0||new_ff_sd_en!==1)$fatal(1,"extended SD alias bank=%h",b);
  manual_addr=(b<<16)|16'hffff;repeat(3)@(negedge clk27);
  if(ma!==0||mm!==1||new_sd_cs_w!==0||new_ff_sd_en!==1)$fatal(1,"extended FFFF alias bank=%h",b);
  isolated=isolated+2;
 end
 manual_mr=1;manual_wr=1;sd_reset=0;repeat(4)@(negedge clk27);sd_reset=1;
 @(negedge clk);manual=0;cpu_reset=1;
 wait(!halt_n);repeat(4)@(negedge clk);
 if(mem[16'hff0]!==8'ha5||reads<512||new_ff_sd_sector!==32'h78563412||new_ff_sd_rstart!==1||new_ff_sd_wstart!==1||new_ff_sd_init!==1)$fatal(1,"CPU program failed marker=%h reads=%d sector=%h",mem[16'hff0],reads,new_ff_sd_sector);
 if(STRESS&&(waits==0||pauses==0))$fatal(1,"missing WAIT/CEN pause coverage");
 $display("PASS SD R11.9 DIV=%d PHASE=%d STRESS=%d reads=%d direct=%d isolated=%d waits=%d pauses=%d",CPU_DIV,PHASE,STRESS,reads,direct_reads,isolated,waits,pauses);$finish;
end
initial begin #200000000;$fatal(1,"SD CPU timeout");end
endmodule
'''
(w/'tb.sv').write_text(ss)
iv=os.environ.get('IVERILOG','iverilog');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[(d,p,s,0) for d in [4,16] for p,s in [(0,0),(3,0),(7,1),(11,1)]]+[(4,0,0,1),(4,0,0,2)]
def run(c):
 d,p,stress,fault=c;name=f'd{d}_p{p}_s{stress}_f{fault}';f=w/(name+'.vvp')
 q=subprocess.run(base+['-g2012','-s','tb_sd_r11_9',f'-Ptb_sd_r11_9.CPU_DIV={d}',f'-Ptb_sd_r11_9.PHASE={p}',f'-Ptb_sd_r11_9.STRESS={stress}',f'-Ptb_sd_r11_9.FAULT={fault}','-o',str(f),str(w/'tb.sv'),str(w/'reference.sv'),str(w/'candidate.sv'),str(r/'verification/cpu_diag.v'),str(r/'fpga/src/ez80_memory_bridge.v')],cwd=r,text=True,capture_output=True);assert q.returncode==0,q.stdout+q.stderr
 q=subprocess.run([os.environ.get('VVP','vvp'),str(f)],cwd=r,text=True,capture_output=True,timeout=1800);out=q.stdout+q.stderr;(w/(name+'.log')).write_text(out)
 if fault:
  assert q.returncode!=0 and 'SD read mismatch' in out,out
  assert ('offset=00000001' if fault==1 else 'offset=00000010') in out,out
 else:assert q.returncode==0 and 'PASS SD R11.9' in out,out
 print('PASS SD '+name,flush=True);return c
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,cases))
(r/'verification_sd_r11_9_result.json').write_text(json.dumps(dict(fresh_runs=8,expected_failure_runs=2,cases=rows,actual_top_register_RTL_extracted=True,actual_G80A_and_bridge=True,read_offsets=256,CPU_reads_per_nominal_run=512,extended_alias_checks_per_run=510,WAIT_and_CEN_pause_profiles=True,reference_write_and_select_state_compared=True,full_SD_card_or_SofaRun_simulated=False,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [r/'fpga/top_ez80.v',r/'doc/r11_7_sd_baseline/top_ez80.v.txt']}),indent=2)+'\n')
