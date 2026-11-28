from pathlib import Path
import subprocess,os,json,concurrent.futures,hashlib
r=Path(__file__).resolve().parents[1];w=r/'verification_differential_r36';w.mkdir(exist_ok=True)
names=[s.split()[0]for s in(r/'RUNALL.BAT').read_text().splitlines()if s.strip()]+['EZ80MX0','EZ80MX1','EZ80MX2','EZ80MA1','EZ80MR4']
if os.environ.get('STRESS'):
 w=w/'stress';w.mkdir(exist_ok=True)
cpu_div=int(os.environ.get('CPU_DIV','4'));assert cpu_div in [2,4,8,16]
if cpu_div!=4:w=w/f'div{cpu_div}';w.mkdir(exist_ok=True)
if os.environ.get('NAMES'):names=os.environ['NAMES'].split(',')
def run(name):
 m=json.loads((r/'hardware_test'/(name+'.json')).read_text());hdr=w/(name+'.vh');blob=r/'hardware_test'/(name+'.COM')
 hdr.write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in m['labels'].items())+f"`define P2_COM_END 16'h{0xff+blob.stat().st_size:04x}\n")
 v=w/(name+'.vvp');c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-I',str(w),f'-DTEST_HEADER="{name}.vh"',f'-DTEST_HEX="hardware_test/{name}.hex"','-s','tb_differential_r27','-o',str(v),str(r/'sim'/('tb_differential_trace_r36.sv'if name=='EZ80MR4'else'tb_differential_r36.sv')),str(r/'verification/cpu_diag.v'),str(r/'verification/cpu_reference.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 if name=='EZ80MR4':c += [str(r/'fpga/src/ez80_trace_mux.v')]
 if os.environ.get('STRESS'):c += [f'-Ptb_differential_r27.CPU_DIV={cpu_div}','-Ptb_differential_r27.PHASE=3','-Ptb_differential_r27.PAUSE_ENABLE=1']
 else:c += [f'-Ptb_differential_r27.CPU_DIV={cpu_div}']
 p=subprocess.run(c,cwd=r,capture_output=True,text=True)
 if p.returncode:out=p.stderr
 else:
  try:p=subprocess.run([os.environ['VVP'],str(v)],cwd=r,capture_output=True,text=True,timeout=1200);out=p.stdout+p.stderr
  except subprocess.TimeoutExpired:out='TIMEOUT';p.returncode=1
 (w/(name+'.log')).write_text(out)
 ok=not p.returncode and 'PASS differential_r27'in out
 print('PASS'if ok else'FAIL',name,out[-600:]if not ok else'',flush=True)
 return dict(COM=name,passed=ok,sha256=hashlib.sha256(blob.read_bytes()).hexdigest(),log=name+'.log')
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(run,names))
(w/('result_'+('_'.join(names) if os.environ.get('NAMES') else 'all')+'.json')).write_text(json.dumps(dict(cases=rows,actual_COM=True,actual_SDRAM_RTL=True,BDOS_EI=True,board=False),indent=2)+'\n')
assert all(x['passed']for x in rows),[x['COM']for x in rows if not x['passed']]
