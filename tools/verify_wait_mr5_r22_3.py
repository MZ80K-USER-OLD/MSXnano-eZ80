from pathlib import Path
import subprocess,os,json,concurrent.futures,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_wait_mr5_r22_3';w.mkdir(exist_ok=True);loc=r.parents[1]
iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'));ivl=os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'));vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
# CPU divider, pause, data-fault, extension, /RUN, legacy feature, trace-link, trace-record, hang
cases=[(4,0,0,1,1,0,0,0,0),(15,1,0,1,1,0,0,0,0),(4,0,1,1,1,0,0,0,0),(4,0,0,0,1,0,0,0,0),(4,0,0,1,0,0,0,0,0),(4,0,0,1,1,1,0,0,0),(4,0,0,1,1,0,1,0,0),(4,0,0,1,1,0,0,1,0),(4,0,0,1,1,0,0,0,1),(4,0,0,1,1,0,0,0,2)]
def run(q):
 d,p,f,e,req,old,link,rec,hang=q;tag='_'.join(map(str,q));v=w/(tag+'.vvp')
 args=[iv,'-B',ivl,'-g2012','-I',str(r/'hardware_test'),'-DTEST_HEADER="EZ80MR5.vh"','-DTEST_HEX="hardware_test/EZ80MR5.hex"','-s','tb_mr5_wait_r22_3','-o',str(v)]+[f'-Ptb_mr5_wait_r22_3.{k}={val}'for k,val in dict(CPU_DIV=d,PAUSE_ENABLE=p,PHASE=7 if p else 0,FAULT=f,EXTENDED=e,RUN_REQUEST=req,LEGACY_FEATURE=old,SUPPORTED=1-old,LINK_FAULT=link,RECORD_FAULT=rec,HANG_AT=hang).items()]+[str(r/n)for n in['sim/tb_mr5_wait_r22_3.sv','verification/cpu_diag.v'if e else'verification/cpu_0.v','sim/sdram_model33.sv','fpga/src/ez80_memory_bridge.v','fpga/src/ez80_wait_monitor.v','fpga/src/memory_ez80.v','fpga/src/ez80_trace_mux.v']]
 a=subprocess.run(args,cwd=r,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([vvp,str(v)],cwd=r,capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr;v.with_suffix('.log').write_text(out)
 if hang:assert not a.returncode and 'PASS injected ACK stall checkpoint'in out,out
 else:
  expected='READY'if not req else'UNSUPPORTED'if not e else'NOT READY'if old else'TRACE LINK FAIL'if link else'FAIL'if f or rec else'PASS'
  assert not a.returncode and'EZ80MR5 R22.2: '+expected in out and'PASS mr5_r22_2'in out,out
  if e and req and not old and not link:
   for s in ['BEFORE_LDHL','HL ACT=010100 EXP=010100','BEFORE_WRITE','WRITE_DONE','BEFORE_A1','A1_DONE','BEFORE_A2','A2_DONE','BEFORE_I1','I1_DONE','BEFORE_I2','I2_DONE','BEFORE_SNAPSHOT','SNAPSHOT_DONE','BEFORE_TRACE','TRACE_DONE','BEFORE_BURST']:assert s in out,(s,out)
   if f:assert'ADDR=010100 EXP=31 ACT=20'in out,out
   elif rec:assert'ADDR=010100 EXP=31 ACT=00'in out,out
   else:assert'W0=650100/31'in out and'W=650100/31 R=650100/31'in out and'W=650100/CE R=650100/CE'in out,out
 print('PASS MR5',q,flush=True);return dict(profile=q,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
(w/'result.json').write_text(json.dumps(dict(profiles=rows,fresh_profiles=len(rows),COM_SHA256=hashlib.sha256((r/'hardware_test/EZ80MR5.COM').read_bytes()).hexdigest(),FPGA_changed=True,simulation_CPU='current R22.3 CPU RTL converted by GHDL (CPU unchanged from R22.2)',hardware_run=False,ack_stalls_are_testbench_injections=True),indent=2)+'\n')
