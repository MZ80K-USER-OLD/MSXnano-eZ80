from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parents[1];w=r/'verification_window_com_r26';w.mkdir(exist_ok=True)
iv=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT']]
cases=[(4,0,0,0,1,1,0),(4,3,1,0,1,1,0),(16,7,1,0,1,1,0),(4,0,0,1,1,1,0),(4,0,0,0,1,0,0),(4,0,0,0,0,1,0),(4,0,0,0,1,1,1)]
if os.environ.get('SMOKE'):cases=cases[:1]
def run(q):
 d,p,s,f,e,req,legacy=q;tag='_'.join(map(str,q));v=w/(tag+'.vvp')
 c=iv+['-g2012','-I',str(r/'hardware_test'),'-DTEST_HEADER="EZ80WIN.vh"','-DTEST_HEX="hardware_test/EZ80WIN.hex"','-s','tb_window_com_r26','-o',str(v)]
 c += [f'-Ptb_window_com_r26.{k}={val}'for k,val in dict(CPU_DIV=d,PHASE=p,PAUSE_ENABLE=s,FAULT=f,EXTENDED=e,RUN_REQUEST=req,LEGACY_FEATURE=legacy,SUPPORTED=1-legacy).items()]
 c += [str(r/'sim/tb_window_com_r26.sv'),str(r/'verification'/('cpu_diag.v'if e else'cpu_0.v')),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 p=subprocess.run(c,cwd=r,capture_output=True,text=True);assert not p.returncode,p.stderr
 p=subprocess.run([os.environ['VVP'],str(v)],cwd=r,capture_output=True,text=True,timeout=240);out=p.stdout+p.stderr;(w/(tag+'.log')).write_text(out)
 exp='READY'if not req else'UNSUPPORTED'if not e else'NOT READY'if legacy else'FAIL stage 0'if f else'PASS'
 assert not p.returncode and 'EZ80WIN R26: '+exp in out and 'PASS window_com_r26' in out,out
 print('PASS WIN actual COM',q,flush=True);return dict(profile=q,expected=exp,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
(w/'result.json').write_text(json.dumps(dict(tests=rows,GOWIN=False,board=False,actual_COM=True,BDOS_EI=True),indent=2)+'\n')
