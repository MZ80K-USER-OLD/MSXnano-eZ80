from pathlib import Path
import subprocess,os,json,concurrent.futures,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_ior_diag_r22_1';w.mkdir(exist_ok=True)
loc=Path('/workspace/scratch/db88d59b2a4d');iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'));ivl=os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'));vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
# name, pause, injected fault(0 none/1 result/2 executable), ext, run, supported, diagnostics
cases=[(n,s,0,1,1,1,1)for n in('EZ80IR0','EZ80IR1','EZ80IR3')for s in(0,1)]+[('EZ80IR3',0,f,1,1,1,1)for f in(1,2)]+[('EZ80IR3',0,0,*q)for q in[(0,1,1,1),(1,0,1,1),(1,1,0,1),(1,1,0,0)]]
if os.environ.get('DIAG_CASES'):cases=[cases[int(i)]for i in os.environ['DIAG_CASES'].split(',')]
def run(q):
 name,pause,f,ext,req,sup,diag=q;tag='_'.join(map(str,q));v=w/(tag+'.vvp');meta=json.loads((r/'hardware_test'/(name+'.json')).read_text());noio=name=='EZ80IR0'
 params=dict(PAUSE_ENABLE=pause,PHASE=7 if pause else 0,CPU_DIV=15 if pause else 4,FAULT=int(f!=0),FAULT_ADDR=0x728200 if f==2 else 0x6e8100,EXTENDED=ext,RUN_REQUEST=req,SUPPORTED=sup,LEGACY_FEATURE=int(not sup and diag),EXPECTED_IO=0 if noio else meta['diagnostic_config']['count'],EXPECTED_PRINTS=3 if f==2 else 6)
 cmd=[iv,'-B',ivl,'-g2012','-I',str(r/'hardware_test'),f'-DTEST_HEADER="{name}.vh"',f'-DTEST_HEX="hardware_test/{name}.hex"','-s','tb_ior_diag_r22_1','-o',str(v)]+[f'-Ptb_ior_diag_r22_1.{k}={val}'for k,val in params.items()]+[str(r/'sim/tb_ior_diag_r22_1.sv'),str(r/'verification'/('cpu_0.v'if not ext else'cpu_diag.v'if diag else'cpu_1.v')),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 p=subprocess.run(cmd,cwd=r,capture_output=True,text=True);assert not p.returncode,p.stderr
 p=subprocess.run([vvp,str(v)],cwd=r,capture_output=True,text=True,timeout=600);out=p.stdout+p.stderr;v.with_suffix('.log').write_text(out)
 exp='READY'if not req else'UNSUPPORTED'if not ext else'NOT READY'if not sup else'FAIL stage 0'if f else'PASS'
 assert not p.returncode and name+' R22.1: '+exp in out and'PASS ior_diag_r22_1'in out,out
 if f==2:assert'ADDR=0E8200 EXP=5B ACT=5A'in out and'CODE_OK'not in out,out
 elif f==1:assert'ADDR=0A8100 EXP=00 ACT=01'in out and'RETURN_OK'in out,out
 elif ext and req and sup:
  for label in('CASE 0','RAM_OK','CODE_OK','ENTER_TEST','RETURN_OK'):assert label in out,out
 print('PASS diagnostic',q,flush=True);return dict(profile=q,expected=exp,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
(w/'result.json').write_text(json.dumps(dict(profiles=rows,fresh_profiles=len(rows),RTL_changed=False,COM_sha256={n:hashlib.sha256((r/'hardware_test'/(n+'.COM')).read_bytes()).hexdigest()for n in('EZ80IR0','EZ80IR1','EZ80IR3')},GOWIN_run=False,hardware_run=False),indent=2)+'\n')
