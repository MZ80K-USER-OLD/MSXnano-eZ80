from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_msx_request_r11_3';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
for diag,fault in [(0,0),(1,0),(1,1),(1,2),(1,3)]:
 target=w/f'd{diag}_f{fault}.vvp'
 args=base+['-g2012','-s','tb_msx_request_r11_3',f'-Ptb_msx_request_r11_3.DIAGNOSTICS={diag}',f'-Ptb_msx_request_r11_3.FAULT={fault}','-o',str(target),str(r/'sim/tb_msx_request_r11_3.sv'),str(r/'verification'/('cpu_diag.v' if diag else 'cpu_1.v')),str(r/'fpga/src/ez80_memory_bridge.v')]
 p=subprocess.run(args,text=True,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
 p=subprocess.run([os.environ.get('VVP','vvp'),str(target)],text=True,capture_output=True,timeout=120);out=p.stdout+p.stderr;target.with_suffix('.log').write_text(out)
 if fault:assert p.returncode!=0 and ('request qualification' if fault==3 else 'MSX isolation') in out,out
 else:assert p.returncode==0 and 'PASS MSX request R11.3' in out,out
 print(('PASS expected fault ' if fault else 'PASS ')+str((diag,fault)),flush=True)
(r/'verification_msx_request_r11_3_result.json').write_text(json.dumps(dict(fresh_runs=2,expected_failure_runs=3,checks_per_positive_run=86016,banks=256,offsets=8,profiles=['memory read','memory write','IO','IACK MC1','IRQ MC2 bank retained','refresh overlay','diagnostic vector','diagnostic write remains MSX'],WAIT_and_CEN_hold=True,qualified_request_register_unit_test=True,full_CPU_execution_proof=False),indent=2)+'\n')
