from pathlib import Path
import subprocess,os,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_cdc_r11_3';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[(shift,1) for shift in (0,2,5,8)]+[(0,0)]
rows=[]
def run(shift,init,fault):
 target=w/f's{shift}_i{init}_f{fault}.vvp'
 args=base+['-g2012','-s','tb_cdc_r11_3','-o',str(target),f'-Ptb_cdc_r11_3.CLOCK_SHIFT={shift}',f'-Ptb_cdc_r11_3.SKIP_INIT={init}',f'-Ptb_cdc_r11_3.FAULT={fault}',str(r/'sim/tb_cdc_r11_3.sv'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 p=subprocess.run(args,cwd=r,text=True,capture_output=True);assert p.returncode==0,p.stderr
 p=subprocess.run([os.environ.get('VVP','vvp'),str(target)],cwd=r,text=True,capture_output=True,timeout=600);out=p.stdout+p.stderr;(target.with_suffix('.log')).write_text(out)
 if fault:assert p.returncode!=0 and (('CDC capture occurred' in out or 'CDC pending published before falling capture' in out) if fault==1 else 'CDC payload changed' in out),out
 else:assert p.returncode==0 and 'PASS CDC R11.3' in out,out
 print('PASS CDC',shift,init,fault,flush=True)
for shift,init in cases:run(shift,init,0);rows.append((shift,init))
for fault in [1,2]:run(0,1,fault)
# Legacy pins must remain identical when extension requests are inactive.
for phase in range(4):
 target=w/f'legacy{phase}.vvp';args=base+['-g2012','-s','tb_memory_compat33','-o',str(target),f'-Ptb_memory_compat33.PHASE={phase}',str(r/'sim/tb_memory_compat33.sv'),str(r/'fpga/src/memory.v'),str(r/'fpga/src/memory_ez80.v')]
 p=subprocess.run(args,cwd=r,text=True,capture_output=True);assert p.returncode==0,p.stderr
 p=subprocess.run([os.environ.get('VVP','vvp'),str(target)],cwd=r,text=True,capture_output=True,timeout=120);assert p.returncode==0 and 'PASS ' in p.stdout,p.stdout+p.stderr;(target.with_suffix('.log')).write_text(p.stdout+p.stderr);print('PASS legacy SDRAM pins',phase,flush=True)
(r/'verification_cdc_r11_3_result.json').write_text(json.dumps(dict(fresh_runs=9,expected_failure_runs=2,real_clock_offsets_ns=[0,2,5,8],payload_minimum_receiver_cycles=2.5,pending_minimum_receiver_cycles=3,payload_capture_edge="falling",payload_stable_until_ack=True,capture_once_per_request=True,VDP_priority_and_refresh=True,legacy_pin_equivalence_runs=4,full_power_on_initialization_runs=1,GOWIN_run=False),indent=2)+'\n')
