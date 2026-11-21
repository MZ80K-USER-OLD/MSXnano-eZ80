"""Compare the candidate with the bundled R24.2 core; no GOWIN area estimate."""
from pathlib import Path
import concurrent.futures, hashlib, json, os, re, shutil, subprocess, sys

r=Path(__file__).resolve().parent.parent
w=r/'verification_regsel_compare';w.mkdir(exist_ok=True)
host=r.parents[1]
g=os.environ.get('GHDL',str(host/'local-ghdl/usr/bin/ghdl') if (host/'local-ghdl/usr/bin/ghdl').exists() else 'ghdl')
env=os.environ.copy()
if (host/'local-ghdl/usr/lib/ghdl/mcode/vhdl').exists():env.setdefault('GHDL_PREFIX',str(host/'local-ghdl/usr/lib/ghdl/mcode/vhdl'))
iv=[os.environ.get('IVERILOG',str(host/'local-iverilog/usr/bin/iverilog') if (host/'local-iverilog/usr/bin/iverilog').exists() else 'iverilog')]
ivroot=os.environ.get('IVL_ROOT',str(host/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'))
if Path(ivroot).exists():iv+=['-B',ivroot]
vvp=os.environ.get('VVP',str(host/'local-iverilog/usr/bin/vvp') if (host/'local-iverilog/usr/bin/vvp').exists() else 'vvp')

def call(cmd,cwd=w,timeout=300):
 p=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
 assert p.returncode==0,p.stdout+p.stderr
 return p.stdout

# Check every binary input combination using equations extracted from the
# original and candidate VHDL, independently of program coverage.
targets=['Load_Upper_Index','Stack_Upper_Index','Pair_Upper_Index','EX_SP_Index','Arith_Target','Arith_Source','Mul_Target']
def selection_entity(src,name,candidate):
 signals=targets+['Pair_Number']+(['Pair_Raw_Index','HL_Resolved_Index','XY_Register_Index'] if candidate else [])
 decl='\n'.join('signal '+n+':std_logic_vector('+('1' if n=='Pair_Number' else '2')+' downto 0);' for n in signals)
 equations=[]
 for n in signals:
  m=re.search(r'(?m)^\s*'+n+r'<=.*?;',src,re.S);assert m,n
  equations.append(m[0])
 return 'library ieee;use ieee.std_logic_1164.all; entity '+name+' is port(IR:in std_logic_vector(7 downto 0);ISet,XY_State:in std_logic_vector(1 downto 0);Alternate:in std_logic;Q:out std_logic_vector(20 downto 0));end; architecture rtl of '+name+' is\n'+decl+'\nbegin\n'+'\n'.join(equations)+'\nQ<='+'&'.join(targets)+';end;\n'
old=(r/'sim/reference/r24_2_regsel/t80_ez80.vhd.txt').read_text()
new=(r/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
tb=selection_entity(old,'sel_ref',False)+selection_entity(new,'sel_dut',True)+'''library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;
entity tb_select is end;architecture test of tb_select is
signal IR:std_logic_vector(7 downto 0);signal pg,xy:std_logic_vector(1 downto 0);signal alt:std_logic;signal qr,qd:std_logic_vector(20 downto 0);
begin
a:entity work.sel_ref port map(IR,pg,xy,alt,qr);
b:entity work.sel_dut port map(IR,pg,xy,alt,qd);
process begin
for op in 0 to 255 loop for page in 0 to 3 loop for prefix in 0 to 3 loop for bank in 0 to 1 loop
IR<=std_logic_vector(to_unsigned(op,8));pg<=std_logic_vector(to_unsigned(page,2));xy<=std_logic_vector(to_unsigned(prefix,2));
if bank=0 then alt<='0';else alt<='1';end if;
wait for 1 ns;assert qr=qd report "selection truth table mismatch" severity failure;
end loop;end loop;end loop;end loop;
report "PASS SELECT_TRUTH 8192 combinations";wait;end process;end;
'''
(w/'tb_select.vhd').write_text(tb)
call([g,'-a','--std=08',str(w/'tb_select.vhd')]);call([g,'-e','--std=08','tb_select'])
call([g,'-r','--std=08','tb_select','--assert-level=error','--stop-time=8193ns'])
print('PASS SELECT_TRUTH 8192 combinations',flush=True)
if '--truth-only' in sys.argv:
 result_path=w/'result.json'
 if result_path.exists():
  result=json.loads(result_path.read_text())
  current={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}
  assert result['source_SHA256']==current,'source changed since cycle comparison'
  result['selection_truth_combinations']=8192
  result_path.write_text(json.dumps(result,indent=2)+'\n')
 sys.exit(0)

def synth(reference,extended):
 q=w/(('reference_build' if reference else 'candidate_build')+('_1' if extended else '_0'));q.mkdir(exist_ok=True)
 for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
  src=r/'fpga/G80A_eZ80'/(n+'_ez80.vhd')
  if reference and n=='t80':src=r/'sim/reference/r24_2_regsel/t80_ez80.vhd.txt'
  call([g,'-a','--std=08','-fsynopsys',str(src)],cwd=q)
 s=call([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches',f'-gDATA_EXTENDED={str(extended).lower()}','G80A_eZ80'],cwd=q)
 s=re.sub(r'\bdo\b','data_out',s)
 needle='  wire [7:0] alu_q;'
 if s.count(needle)==2:
  at=s.index(needle,s.index(needle)+1);s=s[:at]+s[at:].replace(needle,'  wire [7:0] alu_port_q;',1)
  names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1
  s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
 return s

def prepare_model(extended):
 ref=synth(True,extended);dut=synth(False,extended)
 names=re.findall(r'^module (\w+)',ref,re.M)
 ref=re.sub(r'\b('+'|'.join(map(re.escape,sorted(names,key=len,reverse=True)))+r')\b',lambda m:'r242ref_'+m[0],ref)
 reference_path=w/('reference_'+str(int(extended))+'.v');reference_path.write_text(ref)
 start=dut.index('module G80A_eZ80');end=dut.index('endmodule',start)
 head=dut[start:dut.index(');',start)]
 ports=re.findall(r'\b(input|output)\s*(\[\d+:\d+\])?\s*(\w+)',head)
 monitor='\n'
 for direction,dim,n in ports:
  if direction=='output':monitor+=f'wire {dim} ref_{n};\n'
 monitor+='r242ref_G80A_eZ80 shadow('+','.join('.'+n+'('+('ref_'+n if d=='output' else n)+')' for d,dim,n in ports)+');\n'
 monitor+='integer regsel_checks=0;\nalways @(posedge CLK_n or negedge CLK_n) begin\n #0.001;\n if(RESET_n && reset_s && shadow.reset_s)begin\n regsel_checks=regsel_checks+1;\n'
 signals=['regaddra','regaddrb','regaddrc','reg24addrw','reg24addru','load_upper_index','stack_upper_index','pair_upper_index','ex_sp_index','arith_target','arith_source','mul_target','load_target','reg24mask','reg24di','pc','sp','spl','f','acc']
 for n in signals:
  assert re.search(r'\b'+n+r'\b',dut) and re.search(r'\b'+n+r'\b',ref),n
  monitor+=f'if(u0.{n} !== shadow.u0.{n}) $fatal(1,"regsel mismatch {n}");\n'
 monitor+='if(u0.regs.upper_view !== shadow.u0.regs.upper_view) $fatal(1,"upper register state mismatch");\n'
 for direction,dim,n in ports:
  if direction=='output':monitor+=f'if({n} !== ref_{n}) $fatal(1,"bus mismatch {n}");\n'
 monitor+='end\nend\nfinal $display("REGSEL_DIFF checks=%0d",regsel_checks);\n'
 candidate_path=w/('candidate_'+str(int(extended))+'.v')
 model=dut[:end]+monitor+dut[end:]
 previous=w/'candidate.v'
 resume=extended and previous.exists() and previous.read_text()==model
 candidate_path.write_text(model)
 return candidate_path,reference_path,resume

models={True:prepare_model(True),False:prepare_model(False)}

cases=[]
for name in ['data_r3','mem_r4','alu_r5','blk_r6','lea_r8']:
 cases.append((name,dict(PHASE=7),None))
cases.append(('data_r3',dict(PHASE=3,EXTENDED=0),None))
for stem,version in [('ldh',16),('ldx',17)]:
 call(['python3',str(r/f'sim/build_{stem}_unit_r{version}.py')],cwd=r)
 call(['python3',str(r/f'sim/build_{stem}_unit_r{version}.py'),'--irq'],cwd=r)
 for irq in [0,1,2]:cases.append((f'{stem}_unit_r{version}',dict(CPU_DIV=4,PHASE=3,PAUSE=1,IRQ_STRESS=irq),(stem,version,irq)))

def run(item):
 name,params,unit=item;top='tb_'+name
 candidate_model,reference_model,resume=models[bool(params.get('EXTENDED',1))]
 tag=name+'_'+('_'.join(f'{k}{v}' for k,v in params.items()));p=w/(tag+'.vvp')
 cmd=iv+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s',top,'-o',str(p)]
 cmd += [f'-P{top}.{k}={v}' for k,v in params.items()]
 if unit:
  stem,version,irq=unit
  cmd += [f'-DTEST_HEADER="test{"_irq" if irq else ""}.vh"','-I',str(r/f'sim/{stem}_r{version}')]
 cmd += [str(r/'sim'/(top+'.sv')),str(candidate_model),str(reference_model)]
 if not unit:cmd += [str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 log=p.with_suffix('.log')
 if '--resume' in sys.argv and resume and log.exists() and 'PASS '+name in log.read_text():out=log.read_text()
 else:
  call(cmd,cwd=r)
  out=call([vvp,str(p)],cwd=r,timeout=1800);log.write_text(out)
 assert 'PASS '+name in out,out
 m=re.search(r'REGSEL_DIFF checks=(\d+)',out);assert m and int(m[1])>0,out
 print('PASS',tag,'checks='+m[1],flush=True)
 return dict(test=name,parameters=params,checks=int(m[1]),log=p.with_suffix('.log').name)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
result=dict(baseline='R24.2',selection_truth_combinations=8192,tests=rows,total_checks=sum(x['checks'] for x in rows),GOWIN=False,board=False,added_flip_flops=0,source_SHA256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')})
(w/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS total',len(rows),'runs,',result['total_checks'],'edge comparisons')
