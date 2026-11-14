from pathlib import Path
import os,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_rw_diag_r18_3';w.mkdir(exist_ok=True)
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[(4,3,1,0,1,0),(16,0,0,0,1,0),(15,0,0,0,1,0),(15,7,1,0,1,0),(4,0,0,1,1,0),(4,0,0,2,1,0),(4,0,0,0,0,0),(4,0,0,0,1,1)]
def run(q):
 d,p,s,f,req,legacy=q;m=json.loads((r/'hardware_test/EZ80RW2.json').read_text());label='_'.join(map(str,q));v=w/(label+'.vvp')
 args=iv+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-DTEST_HEADER="EZ80RW2.vh"','-DTEST_HEX="hardware_test/EZ80RW2.hex"','-s','tb_rw_diag_r18_2','-o',str(v)]
 args += [f'-Ptb_rw_diag_r18_2.{k}={v}' for k,v in dict(CPU_DIV=d,PHASE=p,PAUSE_ENABLE=s,FAULT=f,RUN_REQUEST=req,LEGACY_FEATURE=legacy,SUPPORTED=1-legacy,EXPECTED_RST_COUNT=0,EXPECTED_PRINTS=m['expected_prints']).items()]
 args += [str(r/'sim/tb_rw_diag_r18_2.sv'),str(r/'verification/cpu_diag.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 a=subprocess.run(args,cwd=r,text=True,capture_output=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ.get('VVP','vvp'),str(v)],cwd=r,text=True,capture_output=True,timeout=1800);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 expected='READY' if not req else 'NOT READY' if legacy else 'FAIL stage '+str(1 if f==1 else 4) if f else 'PASS'
 assert a.returncode==0 and 'EZ80RW2 R18.2: '+expected in out and 'PASS rw_diag_r18_2' in out,out[-2500:]
 if req and not legacy:
  assert 'EZ80RW2 SELF EXP=31 ACT=31' in out,out
  for value in [0x31,0x33,0,1,2,3,0x55,0xaa,0xff]:
   actual=value^2 if f==1 else value
   assert f'EXP={value:02X} IND={actual:02X} ABS={actual:02X}' in out,out
 if f:assert 'ADDR=0A6000 EXP=31 ACT=33' in out,out
 if f==2:assert '3 BLOCK NO DOS' in out and '5 CALL CHECKER' not in out,out
 print('PASS RW diagnostic',q,flush=True);return dict(case=q,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
(r/'verification_rw_diag_r18_3_result.json').write_text(json.dumps(dict(fresh_runs=len(rows),cases=rows,COM_sha256=hashlib.sha256((r/'hardware_test/EZ80RW2.COM').read_bytes()).hexdigest(),FPGA_changed=True,physical_root_cause_confirmed=False,R18_user_hardware=dict(GOWIN_synthesis='PASS',EZ80RS8='freeze and screen-top garbled text',EZ80RS0_R18_1='FAIL stage0 ADDR=0A6000 EXP=31 ACT=33'),BDOS_EI_and_real_IM1_IRQ=True,no_ADL_execution=True,no_RST=True,write_fault_31_to_33_detected=True,read_fault_after_DOS_31_to_33_detected=True),indent=2)+'\n')
