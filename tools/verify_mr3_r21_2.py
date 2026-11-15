from pathlib import Path
import concurrent.futures,subprocess,json,os
r=Path(__file__).resolve().parent.parent;w=r/'verification_mr3_r21_2';w.mkdir(exist_ok=True);loc=r.parent.parent
iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'));ivl=os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'));vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
cases=[(4,0,0,0,1,1),(16,7,1,0,1,1),(4,0,0,1,1,1),(4,0,0,0,0,1),(4,0,0,0,1,0)]
def run(q):
 d,p,s,f,e,run=q;tag='_'.join(map(str,q));v=w/(tag+'.vvp')
 args=[str(iv),'-B',str(ivl),'-g2012','-I',str(r/'hardware_test'),'-DTEST_HEADER="EZ80MR3.vh"',f'-DTEST_HEX="{r}/hardware_test/EZ80MR3.hex"','-s','tb_io2_com_r21','-o',str(v)]
 args += [f'-Ptb_io2_com_r21.{k}={v}'for k,v in dict(CPU_DIV=d,PHASE=p,PAUSE_ENABLE=s,FAULT=f,EXTENDED=e,RUN_REQUEST=run).items()]
 args +=[str(r/'sim/tb_mr3_r21_2.sv'),str(r/'verification'/('cpu_diag.v'if e else'cpu_0.v')),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 a=subprocess.run(args,cwd=r,capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([str(vvp),str(v)],cwd=r,capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;(w/(tag+'.log')).write_text(out)
 expect='READY'if not run else'UNSUPPORTED'if not e else'FAIL'if f else'PASS'
 assert a.returncode==0 and 'EZ80MR3 R21.2: '+expect in out and 'PASS io2_com_r21'in out,out
 if f:assert 'A 07FFFE E31 A1=20 A2=20'in out and 'I1=20 I2=20 HL=07FFFE'in out,out
 if e and run:
  assert 'LOCAL EXP=31 ACT=31'in out
  if f:assert 'W=6BFFFE/31 R=6BFFFE/20'in out and 'W=6BFFFE/CE R=6BFFFE/20'in out,out
  else:
   for addr in ['650100','6B0100','6BFFFE']:
    for val in ['31','CE']:assert f'W={addr}/{val} R={addr}/{val}'in out,out
  for addr in['010100','070100','07FFFE']:
   for wr,val in[('A','31'),('I','CE')]:
    if f and addr=='07FFFE':continue
    assert f'{wr} {addr} E{val} A1={val} A2={val}'in out and f'I1={val} I2={val} HL={addr}'in out,out
 print('PASS MR3',q,flush=True);return dict(profile=q,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
(w/'verification.json').write_text(json.dumps(dict(actual_COM=True,profiles=rows,GOWIN_tested=False,hardware_tested=False),indent=2)+'\n')
