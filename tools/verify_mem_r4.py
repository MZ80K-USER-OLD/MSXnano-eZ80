from pathlib import Path
import os,subprocess,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_mem_r4';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args,timeout=300):
 p=subprocess.run(args,cwd=r,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
labels=json.loads((r/'hardware_test/EZ80MEM.json').read_text())['labels']
cases=[(phase,0,1) for phase in (0,3,7,11)]+[(0,1,1),(3,2,1),(7,3,1),(0,0,0)]
for phase,fault,extended in cases:
 label=f'p{phase}_f{fault}_e{extended}';path=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'hardware_test'),'-s','tb_mem_r4','-o',str(path)]+
     [f'-Ptb_mem_r4.{k}={v}' for k,v in dict(PHASE=phase,FAULT=fault,EXTENDED=extended).items()]+
     [str(r/'sim/tb_mem_r4.sv'),str(r/'verification'/f'cpu_{extended}.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(path)])
 expected='UNSUPPORTED' if not extended else 'FAIL stage '+('1' if fault==1 else '2') if fault else 'PASS'
 assert 'EZ80MEM P1: '+expected in out and 'PASS mem_r4' in out,out
 if fault==1:assert 'ADDR=07FFFE EXP=31 ACT=30' in out,out
 if fault==2:assert 'ADDR=03FFFF EXP=C9 ACT=C8' in out,out
 if fault==3:assert f"ADDR={labels['SNAP']:06X} EXP=56 ACT=57" in out,out
 (w/(label+'.log')).write_text(out);print('PASS mem_r4',label,flush=True)
(r/'verification_mem_r4_result.json').write_text(json.dumps(dict(cases=cases,fresh_runs=len(cases),flash_COM_changed=False,COM_sha256=hashlib.sha256((r/'hardware_test/EZ80MEM.COM').read_bytes()).hexdigest(),EX_reads_before_writes_checked=True,EX_request_count_per_nominal_run=18,gowin_tested=False,hardware_tested=False),indent=2)+'\n')
