from pathlib import Path
import os,re,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_reg24_diff';w.mkdir(exist_ok=True)
b=Path(os.environ.get('R24_REFERENCE',str(r.parents[1]/'r24-work/MSXnano_T80_eZ80_restart_R24/verification/cpu_1.v')))
if not b.is_file():
 q=w/'reference_build';q.mkdir(exist_ok=True);g=os.environ.get('GHDL','ghdl')
 for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
  a=subprocess.run([g,'-a','--std=08','-fsynopsys',str(r/'sim/reference/r24_baseline'/(n+'_ez80.vhd.txt'))],cwd=q,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches','-gDATA_EXTENDED=true','G80A_eZ80'],cwd=q,capture_output=True,text=True);assert not a.returncode,a.stderr
 raw=re.sub(r'\bdo\b','data_out',a.stdout);needle='  wire [7:0] alu_q;'
 if raw.count(needle)==2:
  at=raw.index(needle,raw.index(needle)+1);raw=raw[:at]+raw[at:].replace(needle,'  wire [7:0] alu_port_q;',1)
  names=re.findall(r'assign (alu_n\d+) = alu_q;',raw);assert len(names)==1
  raw=raw.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
 b=q/'cpu_1.v';b.write_text(raw)
ref=b.read_text();names=re.findall(r'^module (\w+)',ref,re.M);rename={n:'r24ref_'+n for n in names}
ref=re.sub(r'\b('+'|'.join(map(re.escape,sorted(names,key=len,reverse=True)))+r')\b',lambda m:rename[m[0]],ref)
(w/'reference.v').write_text(ref)
s=(r/'verification/cpu_1.v').read_text();start=s.index('module G80A_eZ80');end=s.index('endmodule',start);head=s[start:s.index(');',start)]
ports=re.findall(r'\b(input|output)\s*(\[\d+:\d+\])?\s*(\w+)',head)
monitor='\n'
for direction,dim,n in ports:
 if direction=='output':monitor+=f'wire {dim} ref_{n};\n'
monitor+='r24ref_G80A_eZ80 shadow('+','.join('.'+n+'('+('ref_'+n if d=='output' else n)+')'for d,dim,n in ports)+');\n'
monitor+='''integer writes=0,exchanges=0;reg[7:0]seen=0;
always @(posedge CLK_n)if(RESET_n&&shadow.u0.clken&&shadow.reset_s)begin
 if(shadow.u0.upper_port_we)begin
  if((shadow.u0.regweh||shadow.u0.regwel)&&shadow.u0.upper_port_index!==shadow.u0.regaddra)$fatal(1,"upper write address not aligned with low write port: idx=%h addr=%h op=%h mc=%h ts=%h",shadow.u0.upper_port_index,shadow.u0.regaddra,shadow.u0.ir,shadow.u0.mcycle,shadow.u0.tstate);
  writes=writes+1;seen=seen|shadow.u0.upper_port_events;
 end
 if(shadow.u0.exchangedh&&shadow.u0.tstate==3&&shadow.u0.data_long)exchanges=exchanges+1;
end
always @(posedge CLK_n or negedge CLK_n)begin
 #0.001;
 if(RESET_n&&reset_s&&shadow.reset_s)begin
 if(u0.regs.upper_view!==shadow.u0.upper)$fatal(1,"24-bit interface upper state mismatch DUT=%h REF=%h",u0.regs.upper_view,shadow.u0.upper);
 if({u0.pc,u0.sp,u0.spl,u0.f}!=={shadow.u0.pc,shadow.u0.sp,shadow.u0.spl,shadow.u0.f})$fatal(1,"24-bit interface CPU state mismatch");
'''
for direction,dim,n in ports:
 if direction=='output':monitor+=f'if({n}!==ref_{n})$fatal(1,"24-bit interface bus mismatch {n}");\n'
monitor+='end\nend\nfinal $display("REG24_DIFF upper_writes=%0d coverage=%02h exchanges=%0d",writes,seen,exchanges);\n'
(w/'candidate.v').write_text(s[:end]+monitor+s[end:])
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']]if os.environ.get('IVL_ROOT')else[])
cases=['data_r3','mem_r4','alu_r5','blk_r6','lea_r8']
def run(name):
 p=w/(name+'.vvp');cmd=iv+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s','tb_'+name,f'-Ptb_{name}.PHASE=7','-o',str(p),str(r/'sim'/('tb_'+name+'.sv')),str(w/'candidate.v'),str(w/'reference.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 a=subprocess.run(cmd,cwd=r,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([os.environ.get('VVP','vvp'),str(p)],cwd=r,capture_output=True,text=True,timeout=1800);out=a.stdout+a.stderr;p.with_suffix('.log').write_text(out);assert not a.returncode and 'PASS '+name in out,out
 m=re.search(r'REG24_DIFF upper_writes=(\d+) coverage=([0-9a-f]+) exchanges=(\d+)',out);assert m,out
 print('PASS differential',name,m[0],flush=True);return dict(test=name,writes=int(m[1]),coverage=int(m[2],16),exchanges=int(m[3]),output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
mask=0
for row in rows:mask|=row['coverage']
assert mask==255 and any(row['exchanges']>0 for row in rows),(mask,rows)
(w/'result.json').write_text(json.dumps(dict(tests=rows,event_coverage_mask=mask,baseline_SHA256=hashlib.sha256(b.read_bytes()).hexdigest(),GOWIN=False,board=False),indent=2)+'\n')
