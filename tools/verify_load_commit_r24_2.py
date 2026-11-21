"""Atomic pair-load properties plus R24 instruction-boundary/bus comparison."""
from pathlib import Path
import os,re,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/('verification_load_commit_matrix_r24_2' if os.environ.get('ATOMIC_MATRIX') else 'verification_load_commit_r24_2');w.mkdir(exist_ok=True);loc=r.parents[1]
b=Path(os.environ.get('R24_REFERENCE',str(loc/'r24-work/MSXnano_T80_eZ80_restart_R24/verification/cpu_1.v')))
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
ref=b.read_text();names=re.findall(r'^module (\w+)',ref,re.M);rename={n:'r24ref_'+n for n in names};ref=re.sub(r'\b('+'|'.join(map(re.escape,sorted(names,key=len,reverse=True)))+r')\b',lambda m:rename[m[0]],ref);(w/'reference.v').write_text(ref)
s=(r/'verification/cpu_1.v').read_text();at=s.index('module G80A_eZ80');end=s.index('endmodule',at);head=s[at:s.index(');',at)];ports=re.findall(r'\b(input|output)\s*(\[\d+:\d+\])?\s*(\w+)',head)
monitor='\n'
for direction,dim,n in ports:
 if direction=='output':monitor+=f'wire {dim} ref_{n};\n'
monitor+='r24ref_G80A_eZ80 shadow('+','.join('.'+n+'('+('ref_'+n if d=='output'else n)+')'for d,dim,n in ports)+');\n'
monitor+='''integer captures=0,commits=0,boundaries=0,wait_checks=0,held_checks=0,k,bytecount=0;
reg[2:0]families=0,held_target;reg[2:0]held_first,held_last;reg held_sp;reg held_valid=0;
reg[39:0]held_stack_values;reg[23:0]work_before;reg hold_work;reg[7:0]old_events=0;
always @(posedge CLK_n)if(RESET_n&&reset_s)begin
 work_before=u0.ex_sp_read;
 hold_work=!u0.clken || (u0.load_active && u0.mcycle!=1 && u0.tstate==2 && !u0.wait_n);
 if(u0.clken)begin
  old_events=old_events|shadow.u0.upper_port_events;
  if(u0.load_active && u0.mcycle==1 && u0.tstate==3)begin
   captures=captures+1;families=families|u0.exec_control[52:50];bytecount=0;held_valid=1;
   #0.001;held_target=u0.load_target;held_first=u0.load_first;held_last=u0.load_last;held_sp=u0.load_sp;held_stack_values={u0.sp,u0.spl};
  end else if(u0.load_active && u0.mcycle!=1)begin
   if(!held_valid)$fatal(1,"collector used without captured destination");
   if({u0.load_target,u0.load_first,u0.load_last,u0.load_sp}!=={held_target,held_first,held_last,held_sp})$fatal(1,"collector context changed before completion");
   if(held_sp && {u0.sp,u0.spl}!==held_stack_values)$fatal(1,"SP/SPL partially updated before final commit");
   if(u0.reg24exchange)$fatal(1,"load overlaps upper exchange writer");
   if(!u0.load_commit && u0.reg24mask!=0)$fatal(1,"partial architectural register write before final byte");
   if(u0.tstate==2 && !u0.wait_n)wait_checks=wait_checks+1;
   if(u0.tstate==3 && u0.mcycle>=held_first && u0.mcycle<=held_last)bytecount=bytecount+1;
   if(u0.load_commit)begin
    if(bytecount!=(u0.load_three?3:2))$fatal(1,"collector wrong accepted byte count");
    if(u0.reg24addrw!==held_target)$fatal(1,"commit lost captured destination");
    if(held_sp ? u0.reg24mask!==0 : u0.reg24mask!==u0.load_mask)$fatal(1,"commit byte mask / SP routing mismatch");
    if(u0.ex_sp_long)$fatal(1,"collector work register overlaps EX(SP)");
    commits=commits+1;
   end
  end
 end
 #0.002;
 if(hold_work && u0.ex_sp_read!==work_before)$fatal(1,"collector data changed under WAIT/CEN hold");
 if(hold_work)held_checks=held_checks+1;
end
always @(posedge CLK_n or negedge CLK_n)begin
 #0.01;
 if(RESET_n&&reset_s&&shadow.reset_s)begin
  if(u0.pc!==shadow.u0.pc)$fatal(1,"PC / instruction schedule changed");
  // Legacy byte commits finish at the following M1/T1. Compare architectural
  // state after that edge, allowing the intentionally changed partial states.
  if(u0.mcycle==1 && u0.tstate==2 && !u0.frame_active && !shadow.u0.frame_active)begin
   if({u0.sp,u0.spl,u0.f,u0.acc}!=={shadow.u0.sp,shadow.u0.spl,shadow.u0.f,shadow.u0.acc})$fatal(1,"instruction-boundary SP/SPL/F/A mismatch");
   if(u0.regs.upper_view!==shadow.u0.upper)$fatal(1,"instruction-boundary upper register mismatch");
   for(k=0;k<8;k=k+1)if({u0.regs.regsh[k],u0.regs.regsl[k]}!=={shadow.u0.regs.regsh[k],shadow.u0.regs.regsl[k]})$fatal(1,"instruction-boundary low16 mismatch reg=%0d",k);
   boundaries=boundaries+1;
  end
'''
for direction,dim,n in ports:
 if direction=='output':
  condition="(!MREQ_n || !IORQ_n) && !WR_n && "if n in ('DO','data_out')else''
  monitor+=f'if({condition}{n}!==ref_{n})$fatal(1,"bus differential mismatch {n}");\n'
monitor+='''end
end
`ifdef LOAD_COMPARE_FAULT
always @(u0.load_commit)if(u0.load_commit)force u0.reg24addrw=3'b000;else release u0.reg24addrw;
`endif
final $display("LOAD_ATOMIC captures=%0d commits=%0d families=%h boundaries=%0d wait=%0d held=%0d old_events=%02h",captures,commits,families,boundaries,wait_checks,held_checks,old_events);
'''
(w/'candidate.v').write_text(s[:end]+monitor+s[end:])
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']]if os.environ.get('IVL_ROOT')else[])
cases=[('data_r3',0,0),('mem_r4',0,0),('alu_r5',0,0),('blk_r6',0,0),('lea_r8',0,0),('ldh_unit_r16',0,0),('ldh_unit_r16',2,0),('ldx_unit_r17',0,0),('ldx_unit_r17',2,0),('mem_r4',0,1)]
if os.environ.get('ATOMIC_MATRIX'):cases=[('load_matrix_r24_2',0,0)]
if os.environ.get('ATOMIC_TESTS'):cases=[q for q in cases if q[0]in os.environ['ATOMIC_TESTS'].split(',')]
def run(q):
 name,irq,fault=q;v=w/(name+f'_irq{irq}_fault{fault}.vvp');cmd=iv+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s','tb_'+name,'-o',str(v)]
 if fault:cmd+=['-DLOAD_COMPARE_FAULT']
 if name.startswith(('ldh_','ldx_')):
  folder='ldh_r16'if name.startswith('ldh')else'ldx_r17'
  cmd+=['-I',str(r/'sim'/folder),f'-DTEST_HEADER="test{"_irq"if irq else""}.vh"',f'-Ptb_{name}.IRQ_STRESS={irq}',f'-Ptb_{name}.PAUSE=1',f'-Ptb_{name}.CPU_DIV=16',f'-Ptb_{name}.PHASE=7']
 elif name=='load_matrix_r24_2':cmd+=['-Ptb_load_matrix_r24_2.STRESS=1']
 else:cmd+=[f'-Ptb_{name}.PHASE=7']
 cmd +=[str(r/'sim'/('tb_'+name+'.sv')),str(w/'candidate.v'),str(w/'reference.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 a=subprocess.run(cmd,cwd=r,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([os.environ.get('VVP','vvp'),str(v)],cwd=r,capture_output=True,text=True,timeout=2400);out=a.stdout+a.stderr;v.with_suffix('.log').write_text(out)
 if fault:assert a.returncode and 'commit lost captured destination'in out,out
 else:assert not a.returncode and 'PASS '+name in out,out
 m=re.search(r'LOAD_ATOMIC captures=(\d+) commits=(\d+) families=([0-9a-f]+) boundaries=(\d+) wait=(\d+) held=(\d+) old_events=([0-9a-f]+)',out);assert m,out
 print('PASS atomic comparison',q,m[0],flush=True);return dict(test=q,captures=int(m[1]),commits=int(m[2]),families=int(m[3],16),boundaries=int(m[4]),wait=int(m[5]),held=int(m[6]),old_events=int(m[7],16),output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
mask=0
for q in rows:
 if not q['test'][2]:mask|=q['families']
if not os.environ.get('ATOMIC_TESTS'):assert mask==7 and any(q['wait']for q in rows)and any(q['held']for q in rows)
(w/'result.json').write_text(json.dumps(dict(cases=rows,family_coverage=mask,reference='hardware-confirmed R24',baseline_SHA256=hashlib.sha256(b.read_bytes()).hexdigest(),architectural_comparison='instruction boundaries; partial states intentionally differ',external_bus_schedule_compared=True,expected_faults=sum(q[2]for q in cases),GOWIN=False,board=False),indent=2)+'\n')
