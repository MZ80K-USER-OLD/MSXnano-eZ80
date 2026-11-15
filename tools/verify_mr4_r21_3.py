from pathlib import Path
import os,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_mr4_r21_3';w.mkdir(exist_ok=True);loc=r.parent.parent
iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'));ivl=os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'));vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
cases=[(4,0,0,0,1,1,0,0,0),(16,7,1,0,1,1,0,0,0),(4,0,0,1,1,1,0,0,0),(4,0,0,0,0,1,0,0,0),(4,0,0,0,1,0,0,0,0),(4,0,0,0,1,1,1,0,0),(4,0,0,0,1,1,0,1,0),(4,0,0,0,1,1,0,0,1)]
def run(q):
 d,p,s,f,e,req,link,rec,legacy=q;tag='_'.join(map(str,q));v=w/(tag+'.vvp')
 cmd=[iv,'-B',ivl,'-g2012','-I',str(r/'hardware_test'),'-DTEST_HEADER="EZ80MR4.vh"','-DTEST_HEX="hardware_test/EZ80MR4.hex"','-s','tb_io2_com_r21','-o',str(v)]
 cmd +=[f'-Ptb_io2_com_r21.{k}={val}'for k,val in dict(CPU_DIV=d,PHASE=p,PAUSE_ENABLE=s,FAULT=f,EXTENDED=e,RUN_REQUEST=req,LINK_FAULT=link,RECORD_FAULT=rec,LEGACY_FEATURE=legacy,SUPPORTED=1-legacy).items()]
 cmd += [str(r/'sim/tb_mr4_r21_3.sv'),str(r/'verification'/('cpu_diag.v'if e else'cpu_0.v')),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v'),str(r/'fpga/src/ez80_trace_mux.v')]
 a=subprocess.run(cmd,cwd=r,capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([vvp,str(v)],cwd=r,capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;(w/(tag+'.log')).write_text(out)
 exp='READY'if not req else'UNSUPPORTED'if not e else'NOT READY'if legacy else'TRACE LINK FAIL'if link else'FAIL'if f or rec else'PASS'
 assert a.returncode==0 and 'EZ80MR4 R21.3: '+exp in out and 'PASS io2_com_r21'in out,out
 if link:assert 'LINK EXP=55/AA ACT=00/00'in out and 'W='not in out,out
 if e and req and not legacy and not link:
  assert 'LINK EXP=55/AA ACT=55/AA'in out
  if rec:assert 'W=000000/00 R=000000/00'in out and 'A 07FFFE E31 A1=31 A2=31'in out,out
  elif f:assert 'W=6BFFFE/31 R=6BFFFE/20'in out and 'A 07FFFE E31 A1=20 A2=20'in out,out
  else:
   for logical,physical in [('010100','650100'),('070100','6B0100'),('07FFFE','6BFFFE')]:
    for wr,val in [('A','31'),('I','CE')]:assert f'{wr} {logical} E{val} A1={val} A2={val}'in out and f'I1={val} I2={val} HL={logical}'in out and f'W={physical}/{val} R={physical}/{val}'in out,out
 print('PASS MR4',q,flush=True);return dict(profile=q,expected=exp,output=out)
selected=cases if not os.environ.get('CASE_INDEX')else[cases[int(i)]for i in os.environ['CASE_INDEX'].split(',')]
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,selected))
if os.environ.get('CASE_INDEX'):
 rows=[]
 for q in cases:
  out=(w/('_'.join(map(str,q))+'.log')).read_text();assert 'PASS io2_com_r21'in out and 'FATAL:'not in out,out
  rows.append(dict(profile=q,output=out))
(w/'result.json').write_text(json.dumps(dict(verified_profiles=len(rows),fresh_profiles_this_invocation=len(selected),COM_sha256=hashlib.sha256((r/'hardware_test/EZ80MR4.COM').read_bytes()).hexdigest(),profiles=rows,GOWIN_run=False,hardware_run=False),indent=2)+'\n')
