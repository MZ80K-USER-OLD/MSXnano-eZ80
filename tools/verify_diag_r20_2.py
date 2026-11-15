from pathlib import Path
import os,subprocess,json,hashlib,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_diag_r20_2';w.mkdir(exist_ok=True)
# Board-derived clocks and actual PINFILTER + edge detector; long timer scaled 128x.
base=(r/'sim/tb_sleep_board_r20_2.sv').read_text()
a=base.index('    initial if($test$plusargs("CLOCK_DEBUG"))');b=base.index('    initial if($test$plusargs("TRACE"))',a);base=base[:a]+base[b:]
base=base.replace('module tb_sleep_board_r20_2;', 'module tb_diag_r20_2;').replace('cpu.diag_select==8\'hce','cpu.diag_select==8\'hf2')
base=base.replace('rst_entries!=0','rst_entries!=0')
base=base.replace('if(dos_acks!=1)',"if(dos_acks!=((!EXTENDED||!RUN_REQUEST||!SUPPORTED)?1:FAULT?2:`EXPECTED_SLEEPS+1))")
base=base.replace('if(bdos_calls!=1)',"if(bdos_calls!=((!EXTENDED||!RUN_REQUEST||!SUPPORTED)?1:FAULT?2:`EXPECTED_SLEEPS+1))")
base=base.replace('sleep_entries!=20||sleep_ticks<140','sleep_entries!=`EXPECTED_SLEEPS||sleep_ticks<24')
base=base.replace('.Sleep_Timer(slow_timer)', '.Sleep_Timer(mem.FreeCounter[8])')
base=base.replace('PASS sleep_com_r20','PASS diag_r20_2')
base=base.replace('    integer rst_entries=0;', "    integer release_requests=0,fetch_acks=0;reg release_was_pending=0;\n    always @(posedge c54)if(reset_n)begin\n        if(cpu.diag_select==8'hd6&&!release_was_pending)release_requests=release_requests+1;\n        release_was_pending<=cpu.diag_select==8'hd6;\n        if(cpu.diag_select==8'hd5&&cpu.sleep_i)$fatal(1,\"completion before wake\");\n        if(real_ce&&cpu.diag_select==8'hd6&&!cpu.sleep_i&&cpu.mcycle==1&&cpu.tstate==2&&cpu.wait_s)fetch_acks=fetch_acks+1;\n    end\n    integer rst_entries=0;")
base=base.replace('            $display("PASS diag_r20_2', '            if(EXTENDED&&RUN_REQUEST&&SUPPORTED&&!FAULT&&(release_requests!=`EXPECTED_SLEEPS||fetch_acks!=`EXPECTED_SLEEPS))$fatal(1,"release handshake coverage");\n            $display("PASS diag_r20_2')

(r/'sim/tb_diag_r20_2.sv').write_text(base)
profiles=[(0,1,1,0,0),(1,1,1,0,0),(0,0,1,0,0),(0,1,0,0,0),(0,1,1,1,0),(0,1,1,0,1)]
# fault,extensions,/RUN,legacy-feature,nodiag; plus one delayed receiver per binary.
jobs=[(n,*q,0)for n in ['EZ80SL2','EZ80RF2']for q in profiles]+[(n,0,1,1,0,0,1)for n in ['EZ80SL2','EZ80RF2']]
if os.environ.get('SMOKE'):jobs=jobs[:1]
def run(q):
 n,f,e,req,legacy,nd,delay=q;label='_'.join(map(str,q));v=w/(label+'.vvp');sleeps=4 if n=='EZ80SL2'else 2;meta=json.loads((r/'hardware_test'/(n+'.json')).read_text())
 assert hashlib.sha256((r/'hardware_test'/(n+'.COM')).read_bytes()).hexdigest()==meta['sha256']
 cmd=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-I',str(r/'hardware_test'),'-DTEST_HEADER="'+n+'.vh"','-DTEST_HEX="hardware_test/'+n+'.hex"','-DEXPECTED_SLEEPS='+str(sleeps),'-s','tb_diag_r20_2','-o',str(v)]
 cmd +=[f'-Ptb_diag_r20_2.{k}={x}'for k,x in dict(FAULT=f,EXTENDED=e,RUN_REQUEST=req,SUPPORTED=int(not(legacy or nd)),LEGACY_FEATURE=legacy,RELEASE_DELAY=delay).items()]
 cmd +=[str(r/'sim/tb_diag_r20_2.sv'),str(r/'verification'/('cpu_0.v'if not e else'cpu_1.v'if nd else'cpu_diag.v')),str(r/'fpga/tn_vdp_v3_v9958/src/pinfilter.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/memory_ez80.v'),str(r/'fpga/src/ez80_memory_bridge.v')]
 a=subprocess.run(cmd,capture_output=True,text=True);assert a.returncode==0,a.stderr
 with (w/(label+'.log')).open('w')as log:a=subprocess.run([os.environ['VVP'],str(v)],cwd=r,stdout=log,stderr=subprocess.STDOUT,text=True,timeout=1800)
 out=(w/(label+'.log')).read_text()
 status='READY'if not req else'UNSUPPORTED'if not e else'NOT READY'if legacy or nd else'FAIL stage 0'if f else'PASS'
 assert a.returncode==0 and n+' R20.2: '+status in out and'PASS diag_r20_2'in out,out
 print('PASS diag R20.2',q,flush=True);return dict(profile=q,status=status,sha256=meta['sha256'],receiver_delay_injected=bool(delay))
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,jobs))
(r/'verification_diag_r20_2_result.json').write_text(json.dumps(dict(fresh_runs=len(rows),cases=rows,fractional_external_CPU_clock=True,SDRAM_model_clock_phase_fixed=True,PINFILTER_Z_hold_abstraction=True,external_CPU_clock=True,long_timer_acceleration=128,physical_failure_reproduced=False),indent=2)+'\n')
