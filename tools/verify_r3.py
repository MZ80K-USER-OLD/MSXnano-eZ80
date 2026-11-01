from pathlib import Path
import os,subprocess,re,json,hashlib,itertools
r=Path(__file__).resolve().parent.parent; w=r/'verification';w.mkdir(exist_ok=True)
g=os.environ.get('GHDL','ghdl');iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp')
base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args,cwd=r,timeout=240):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(' '.join(args)+'\n'+p.stdout+'\n'+p.stderr)
 return p.stdout+p.stderr
def compile_cpu(folder,ext=True):
 folder.mkdir(exist_ok=True)
 for fn,suffix in [('G80A',''),('G80A_eZ80','_ez80')]:
  for n in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):
   run([g,'-a','--std=08','-fsynopsys',str(r/'fpga'/fn/(n+suffix+'.vhd'))],folder)
run(['python3','hardware_test/build_data_r3.py'])
compile_cpu(w)
run([g,'-a','--std=08','-fsynopsys',str(r/'sim/tb_locked_r1.vhd')],w)
locked=[]
for vals in itertools.product(('false','true'),repeat=4):
 args=[f'-g{k}={v}' for k,v in zip(('EXTENSIONS','INSERT_WAIT','SEED','CARRY_IN'),vals)]
 out=run([g,'-r','--std=08','-fsynopsys','tb_locked_r1']+args+['--assert-level=error'],w)
 assert 'PASS locked boot' in out;locked.append(' '.join(args)+'\n'+out)
(w/'locked.log').write_text(''.join(locked));print('PASS locked compatibility',len(locked),flush=True)
for ext in (True,False):
 needle='  wire [7:0] alu_q;'
 p=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches',f'-gDATA_EXTENDED={str(ext).lower()}','G80A_eZ80'],cwd=w,text=True,capture_output=True)
 assert p.returncode==0,p.stderr
 s=re.sub(r'\bdo\b','data_out',p.stdout)
 if s.count(needle)==2:
  j=s.index(needle,s.index(needle)+1);s=s[:j]+s[j:].replace(needle,'  wire [7:0] alu_port_q;',1)
  names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1
  s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
 (w/f'cpu_{int(ext)}.v').write_text(s);(w/f'conversion_{int(ext)}.log').write_text(p.stderr)
print('PASS CPU conversion for simulation (not Gowin)',flush=True)
common=[str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
cases=[(phase,0,1) for phase in (0,3,7,11)]+[(7,1,1),(0,2,1),(3,3,1),(7,4,1),(3,5,1),(0,0,0)]
logs=[]
for phase,fault,ext in cases:
 label=f'p{phase}_f{fault}_e{ext}'
 run(base+['-g2012','-I',str(r/'hardware_test'),'-s','tb_data_r3','-o',str(w/(label+'.vvp')),f'-Ptb_data_r3.PHASE={phase}',f'-Ptb_data_r3.FAULT={fault}',f'-Ptb_data_r3.EXTENDED={ext}']+[str(r/'sim/tb_data_r3.sv'),str(w/f'cpu_{ext}.v')]+common)
 out=run([vvp,str(w/(label+'.vvp'))],timeout=600)
 expected='UNSUPPORTED' if not ext else ('FAIL stage '+('1' if fault==1 else '7' if fault==3 else 'A' if fault==4 else 'B' if fault==5 else '3')) if fault else 'PASS'
 assert 'EZ80D3 R3: '+expected in out and 'PASS data_r3' in out,out
 if fault==1:assert 'ADDR=1A8000 EXP=4A ACT=4B' in out,out
 if fault==2:assert 'ADDR=030000 EXP=96 ACT=97' in out,out
 if fault==3:assert 'ADDR=04FFFE EXP=56 ACT=57' in out,out
 if fault==4:assert 'ADDR=07FFFE EXP=56 ACT=57' in out,out
 if fault==5:assert 'ADDR=060102 EXP=A7 ACT=A6' in out,out
 (w/(label+'.log')).write_text(out);logs.append((label,out));print('PASS',label,flush=True)
# Partial syntax only: other languages/vendor blocks/peripherals not elaborated.
out=run(base+['-g2012','-i','-tnull','-s','top','-I',str(r/'fpga/src'),str(r/'fpga/top_ez80.v')]+common[1:],r/'fpga')
(w/'top_syntax.log').write_text(out+'PASS partial top Verilog syntax only\n')
paths=list((r/'fpga/G80A_eZ80').glob('*.vhd'))+[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'fpga/top_ez80.v',r/'fpga/tang20k.sdc',r/'hardware_test/EZ80D3.COM']
(r/'verification_result.json').write_text(json.dumps(dict(series='restart R3',locked_comparison_runs=len(locked),actual_COM_simulation_runs=len(cases),cases=cases,pc_bits=16,sps_bits=16,spl_bits=24,gowin_tested=False,hardware_tested=False,full_DOS_simulated=False,full_BIOS_boot_simulated=False,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}),indent=2)+'\n')
print('PASS R3 verification complete',flush=True)
