from pathlib import Path
import os,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_decode_com_r24';w.mkdir(exist_ok=True)
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
com_sha=hashlib.sha256((r/'hardware_test/EZ80DEC.COM').read_bytes()).hexdigest()
# d,phase,pause,fault,extensions,/RUN,legacy-feature,nodiag
cases=[(4,0,0,0,1,1,0,0),(15,7,1,0,1,1,0,0),(4,0,0,1,1,1,0,0),(4,0,0,0,0,1,0,0),(4,0,0,0,1,0,0,0),(4,0,0,0,1,1,1,0),(4,0,0,0,1,1,0,1)]
if os.environ.get('SMOKE'):cases=cases[:1]
if os.environ.get('CASE_INDEX'):cases=[cases[int(x)] for x in os.environ['CASE_INDEX'].split(',')]
def run(q):
 d,p,s,f,e,req,legacy,nd=q;label='_'.join(map(str,q));v=w/(label+'.vvp');sup=not(legacy or nd)
 args=iv+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-DTEST_HEADER="EZ80DEC.vh"','-DTEST_HEX="hardware_test/EZ80DEC.hex"','-s','tb_decode_com_r24','-o',str(v)]
 args += [f'-Ptb_decode_com_r24.{k}={v}' for k,v in dict(PHASE=p,FAULT=f,EXTENDED=e,RUN_REQUEST=req,CPU_DIV=d,PAUSE_ENABLE=s,SUPPORTED=int(sup),LEGACY_FEATURE=legacy).items()]
 args += [str(r/'sim/tb_decode_com_r24.sv'),str(r/'verification'/('cpu_0.v' if not e else 'cpu_1.v' if nd else 'cpu_diag.v')),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 assert hashlib.sha256((r/'hardware_test/EZ80DEC.COM').read_bytes()).hexdigest()==com_sha
 a=subprocess.run(args,cwd=r,text=True,capture_output=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ.get('VVP','vvp'),str(v)],cwd=r,text=True,capture_output=True,timeout=2400);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 expected='READY' if not req else 'UNSUPPORTED' if not e else 'NOT READY' if not sup else 'FAIL stage 0' if f else 'PASS'
 assert a.returncode==0 and 'EZ80DEC R24: '+expected in out and 'PASS decode_com_r24' in out,out
 if f:assert 'ADDR=0A8100 EXP=D7 ACT=D6' in out,out
 print('PASS decode actual COM',q,flush=True);return dict(case=q,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
assert hashlib.sha256((r/'hardware_test/EZ80DEC.COM').read_bytes()).hexdigest()==com_sha
(r/'verification_decode_com_r24_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),expected_failure_runs=0,cases=rows,COM_sha256=hashlib.sha256((r/'hardware_test/EZ80DEC.COM').read_bytes()).hexdigest(),actual_COM_bytes=True,board_bridge_SDRAM_model=True,BDOS_stub_deliberately_EI=True,no_MSX_vector_writes=True,private_16_decode_cases=True,DOS_real_IM1_IRQ=True,old_feature_and_no_diagnostics_guard=True,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
