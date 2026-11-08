from pathlib import Path
import os,re,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_upper_r12';w.mkdir(exist_ok=True)
g=os.environ.get('GHDL','ghdl')
# Convert the exact saved R11.9 CPU, rather than writing a behavioral model.
q=w/'reference_build';q.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 src=r/'doc/r11_10_mbase_baseline'/(n+'_ez80.vhd.txt')
 out=subprocess.run([g,'-a','--std=08','-fsynopsys',str(src)],cwd=q,text=True,capture_output=True);assert out.returncode==0,out.stderr
a=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches','-gDATA_EXTENDED=true','G80A_eZ80'],cwd=q,text=True,capture_output=True);assert a.returncode==0,a.stderr
s=re.sub(r'\bdo\b','data_out',a.stdout);needle='  wire [7:0] alu_q;'
if s.count(needle)==2:
 at=s.index(needle,s.index(needle)+1);s=s[:at]+s[at:].replace(needle,'  wire [7:0] alu_port_q;',1);names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1;s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
modules=re.findall(r'^module (\w+)',s,re.M);assert 'G80A_eZ80' in modules
rename={n:'reference_'+n for n in modules};s=re.sub(r'\b('+'|'.join(map(re.escape,sorted(modules,key=len,reverse=True)))+r')\b',lambda m:rename[m[0]],s)
(w/'reference.v').write_text(s)
candidate=(r/'verification/cpu_1.v').read_text();at=candidate.index('module G80A_eZ80');end=candidate.index('endmodule',at);head=candidate[at:candidate.index(');',at)]
ports=[]
for dr,dim,n in re.findall(r'\b(input|output)\s*(\[\d+:\d+\])?\s*(\w+)',head):ports.append((dr,dim,n))
assert len(ports)==24,len(ports)
monitor='\n// R11.10 simulation-only shadow CPU, no DUT RTL dependency.\n'
for dr,dim,n in ports:
 if dr=='output':monitor+=f'wire {dim} ref_{n};\n'
monitor+='reference_G80A_eZ80 shadow('+','.join('.'+n+'('+('ref_'+n if dr=='output' else n)+')' for dr,dim,n in ports)+');\n'
monitor+='''reg[7:0] seen_upper=0;integer swap_count=0;integer k,n_events;
always @(posedge CLK_n)if(RESET_n&&u0.clken)begin
 n_events=0;for(k=0;k<8;k=k+1)if(u0.upper_port_events[k])n_events=n_events+1;
 if(n_events>1)$fatal(1,"ordinary upper write events overlap");
 seen_upper=seen_upper|u0.upper_port_events;
 if(u0.extensions_enabled&&u0.data_long&&u0.exchangedh&&u0.tstate==3)swap_count=swap_count+1;
end
always @(posedge CLK_n or negedge CLK_n)begin
 #0.001;
 if(RESET_n&&reset_s)begin
  if(u0.upper!==shadow.u0.upper)$fatal(1,"Upper differential mismatch candidate=%h reference=%h",u0.upper,shadow.u0.upper);
  if({u0.spl,u0.pc,u0.f}!=={shadow.u0.spl,shadow.u0.pc,shadow.u0.f})$fatal(1,"CPU state differential mismatch");
'''
for dr,dim,n in ports:
 if dr=='output':monitor+=f'if({n}!==ref_{n})$fatal(1,"bus differential mismatch {n}");\n'
monitor+='end\nend\nfinal $display("UPPER_COVERAGE=%02x EXCHANGE=%0d",seen_upper,swap_count);\n'
for fault in [0,1,2]:
 force='' if not fault else "initial force u0.upper_port_data=8'hff;\n" if fault==1 else "initial force u0.upper_port_index=3'b111;\n"
 (w/f'candidate_f{fault}.v').write_text(candidate[:end]+monitor+force+candidate[end:])
# This finite opcode/ISet lemma establishes ordinary-event exclusivity without
# relying on which pairs of controls happened to occur in the COM runs.
max_events=0
for iset in range(4):
 for op in range(256):
  families=[iset==0 and op in [0x22,0x2a] or iset==2 and op>>6==1 and op&7==3,
   iset==2 and op in [2,3,0x12,0x13,0x22,0x23,0x32,0x33,0x54,0x55],
   iset==0 and op>>6==0 and op&15==9 or iset==2 and op>>6==1 and op&7==2,
   iset==0 and op==0xe3,
   iset==2 and op>>5==5 and (op>>1)&3==0,
   iset==0 and op>>6==0 and op&15 in [3,11],
   iset==0 and op>>6==3 and op&15==1,
   iset==0 and op>>6==0 and op&15==1]
  max_events=max(max_events,sum(families));assert sum(families)<=1,(iset,op,families)
iv=os.environ.get('IVERILOG','iverilog');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[('data_r3',7,0),('mem_r4',3,0),('alu_r5',7,0),('blk_r6',7,0),('lea_r8',7,0),('corners_r4',7,0),('data_r3',0,1),('data_r3',0,2)]
# Corner fixture is internal; never overwrites the preloaded COM set.
subprocess.run(['python3',str(r/'sim/build_corners_r4.py')],cwd=r,check=True,capture_output=True)
def run(case):
 name,phase,fault=case;f=w/(name+f'_p{phase}_f{fault}.vvp');inc=r/'sim/corners' if name=='corners_r4' else r/'hardware_test'
 cmd=base+['-g2012','-I',str(inc),'-I',str(r/'sim'),'-s','tb_'+name,f'-Ptb_{name}.PHASE={phase}','-o',str(f),str(r/'sim'/('tb_'+name+'.sv')),str(w/f'candidate_f{fault}.v'),str(w/'reference.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 p=subprocess.run(cmd,cwd=r,text=True,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
 p=subprocess.run([os.environ.get('VVP','vvp'),str(f)],cwd=r,text=True,capture_output=True,timeout=600);out=p.stdout+p.stderr;f.with_suffix('.log').write_text(out)
 if fault:assert p.returncode!=0 and 'Upper differential mismatch' in out,out
 else:assert p.returncode==0 and 'PASS '+name in out,out
 m=re.search(r'UPPER_COVERAGE=([0-9a-f]+) EXCHANGE=(\d+)',out);assert m,out
 print('PASS Upper reference',case,flush=True);return dict(case=case,events_seen=int(m[1],16),exchange_count=int(m[2]))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
coverage=0;swaps=0
for j in rows:
 if j['case'][2]==0:coverage|=j['events_seen'];swaps+=j['exchange_count']
assert coverage==255 and swaps>0,(coverage,swaps)
(r/'verification_upper_r12_result.json').write_text(json.dumps(dict(fresh_runs=6,expected_failure_runs=2,cases=rows,event_coverage_mask=coverage,exchange_coverage=swaps,all_64_upper_bits_compared_each_clock_edge=True,external_bus_PC_SPL_flags_compared=True,one_ordinary_event_proof_opcode_ISet_combinations=1024,maximum_event_family_count=max_events,baseline='R11.10 CPU saved source; comparison programs keep MBASE zero',GOWIN_run=False,hardware_run=False,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
