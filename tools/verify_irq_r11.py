from pathlib import Path
import os,subprocess,json,hashlib,sys,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_irq_r11';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=600)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
rows=[]
names=sys.argv[1:] or ['EZ80IRQ','EZ80IM2','EZ80NMI','EZ80I16','EZ80RST','EZ80MAD','EZ80MIX','EZ80MB','EZ80TST','EZ80LDH','EZ80LDX']
jobs=[]
for name in names:
 supported=name in ['EZ80IRQ','EZ80IM2','EZ80NMI','EZ80I16','EZ80RST','EZ80MB','EZ80MAD','EZ80MIX','EZ80TST']
 cases=[(0,0,1,1,16,0)] if os.environ.get('SMOKE') else [(p,0,1,1,16,0) for p in (0,7)]+[(0,1,1,1,16,0),(0,0,1,0,16,0),(0,0,0,1,16,0),(3,0,1,1,4,0),(7,0,1,1,4,1)] if supported else [(0,0,1,1,16,0)]
 for q in cases:jobs.append((name,supported,q))
def check(job):
 name,supported,q=job;phase,fault,ext,request,div,pause=q
 label=f'{name}_p{phase}_f{fault}_e{ext}_r{request}_d{div}_pause{pause}';p=w/(label+'.vvp')
 addr=0x670401 if name=='EZ80NMI' else 0x670400
 run(base+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),f'-DTEST_HEADER="{name}.vh"',f'-DTEST_HEX="hardware_test/{name}.hex"','-s','tb_irq_r11','-o',str(p)]+[f'-Ptb_irq_r11.{k}={v}' for k,v in dict(PHASE=phase,FAULT=fault,EXTENDED=ext,RUN_REQUEST=request,CPU_DIV=div,PAUSE_ENABLE=pause,SUPPORTED=int(supported),FAULT_ADDR=addr).items()]+[str(r/'sim/tb_irq_r11.sv'),str(r/'verification'/('cpu_diag.v' if ext else 'cpu_0.v')),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(p)])
 expected='READY' if not request else 'UNSUPPORTED' if not ext else 'NOT READY' if not supported else ('FAIL stage B' if name=='EZ80MIX' else 'FAIL stage A') if fault else 'PASS'
 assert name+' P2: '+expected in out and 'PASS irq_r11' in out,out
 if fault:assert 'ADDR='+f'{addr-0x640000:06X}' in out and 'EXP=' in out and 'ACT=' in out,out
 (w/(label+'.log')).write_text(out);print('PASS',label,flush=True);return dict(name=name,phase=phase,fault=fault,extended=ext,request=request,div=div,pause=pause)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(check,jobs))
(r/'verification_irq_r11_result.json').write_text(json.dumps(dict(fresh_runs=len(rows),cases=rows,COM_sha256={n:hashlib.sha256((r/'hardware_test'/(n+'.COM')).read_bytes()).hexdigest() for n in names},GOWIN_run=False,hardware_run=False),indent=2)+'\n')
