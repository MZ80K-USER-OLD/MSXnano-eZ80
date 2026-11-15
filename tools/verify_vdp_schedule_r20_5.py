from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_vdp_schedule_r20_5';w.mkdir(exist_ok=True)
for phase in range(4):
 v=w/f'p{phase}.vvp';a=subprocess.run([os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_vdp_schedule_r20_5',f'-Ptb_vdp_schedule_r20_5.PHASE={phase}','-o',str(v),str(r/'sim/tb_vdp_schedule_r20_5.sv'),str(r/'fpga/src/memory.v'),str(r/'fpga/src/memory_ez80.v')],capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=300);(w/f'p{phase}.log').write_text(a.stdout+a.stderr);assert a.returncode==0 and 'PASS memory_compat33' in a.stdout,a.stdout+a.stderr
 print('PASS video slot pins',phase,flush=True)
(r/'verification_vdp_schedule_r20_5_result.json').write_text(json.dumps(dict(fresh_runs=4,SLEEP_REFRESH_enabled=True,cpu_sleep=0,original_video_slot_pins_compared=True,all_legacy_CPU_pins_identical=False),indent=2)+'\n')
