from pathlib import Path
import subprocess,os,json,concurrent.futures,hashlib
r=Path(__file__).resolve().parent.parent;loc=r.parents[1];w=r/'verification_pipeline_final_r22_4';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'));ivl=os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'));vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
cases=[{},dict(CPU_DIV=15,PAUSE_ENABLE=1,PHASE=7),dict(FAULT=1),dict(FAULT=2),dict(PIPE_FAULT=1),dict(PIPE_FAULT=2),dict(RUN_REQUEST=0),dict(EXTENDED=0),dict(OLD_PIPE=1),dict(LINK_FAULT=1),dict(HANG_AT=2),dict(SHARED_LEGACY=1,CPU_DIV=16),dict(MATRIX=1)]
def run(index_case):
 i,c=index_case;c=c.copy();matrix=c.pop('MATRIX',0);name='EZ80MX6' if matrix else 'EZ80MR6';meta=json.loads((r/'hardware_test'/(name+'.json')).read_text());params=dict(CPU_DIV=4,PAUSE_ENABLE=0,PHASE=0,FAULT=0,PIPE_FAULT=0,RUN_REQUEST=1,EXTENDED=1,OLD_PIPE=0,LINK_FAULT=0,HANG_AT=0);params.update(c)
 top='tb_mr6_r22_4';v=w/f'case_{i:02}.vvp'
 cmd=[iv,'-B',ivl,'-g2012','-I',str(r/'hardware_test'),f'-DTEST_HEADER="{name}.vh"',f'-DTEST_HEX="hardware_test/{name}.hex"','-s',top,'-o',str(v)]+[f'-P{top}.{k}={val}'for k,val in params.items()]+[str(r/p)for p in['sim/tb_mr6_r22_4.sv','verification/cpu_diag.v'if params['EXTENDED']else'verification/cpu_0.v','sim/sdram_model33.sv','fpga/src/ez80_memory_bridge.v','fpga/src/ez80_wait_monitor.v','fpga/src/memory_ez80.v','fpga/src/ez80_trace_mux.v']]
 p=subprocess.run(cmd,cwd=r,capture_output=True,text=True);assert not p.returncode,p.stderr
 p=subprocess.run([vvp,str(v)],cwd=r,capture_output=True,text=True,timeout=600);out=p.stdout+p.stderr;v.with_suffix('.log').write_text(out)
 assert not p.returncode,out
 if params['HANG_AT']:assert 'PASS injected ACK stall checkpoint'in out,out
 else:
  expected='READY'if not params['RUN_REQUEST']else'UNSUPPORTED'if not params['EXTENDED']else'NOT READY'if params['OLD_PIPE']else'TRACE LINK FAIL'if params['LINK_FAULT']else'FAIL'if params['FAULT']or params['PIPE_FAULT']else'PASS'
  assert name+' R22.4: '+expected in out and 'PASS mr6_r22_4'in out,out
  if expected in ('PASS','FAIL'):
   assert out.count('\nCAP=')==len(meta['rows']) and out.count('BEGIN ')==len(meta['rows']),out
   if params['FAULT']==1:assert'ADDR=010100 EXP=31 ACT=20'in out,out
   if params['FAULT']==2:assert'ADDR=010100 EXP=31 ACT=00'in out and'CAP=00 CMD=00 RAM=00 RET=00'in out and'CAP=08 CMD=08 RAM=08 RET=08'in out,out
   if expected=='PASS':
    for row in meta['rows']:
     assert f'{row["writer"]} ADDR={row["address"]} EXP={row["expected"]} A1={row["expected"]} A2={row["expected"]} I1={row["expected"]} I2={row["expected"]}'in out,out
     assert f'WCAP={row["physical"]}'in out,out
 print('PASS MR6',i,c,flush=True);return dict(program=name,profile=params,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,enumerate(cases)))
(w/'result.json').write_text(json.dumps(dict(profiles=rows,fresh_profiles=len(rows),MR6_rows=2,MX6_rows=18,shared_legacy_RAM_profile=True,COM_sha256=hashlib.sha256((r/'hardware_test/EZ80MR6.COM').read_bytes()).hexdigest(),GOWIN=False,hardware=False,faults_are_simulation_injections=True),indent=2)+'\n')
