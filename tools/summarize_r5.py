from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
previous=r/'verification_regression_R4_on_R5.json'
if not previous.exists():
 j=json.loads((r/'verification_result.json').read_text());assert j['series']=='restart R4'
 previous.write_text(json.dumps(j,indent=2)+'\n')
a=json.loads(previous.read_text());b=json.loads((r/'verification_alu_r5_result.json').read_text());c=json.loads((r/'verification_arith_corners_r5_result.json').read_text())
for path,h in a['sha256'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==h,path
paths=list((r/'fpga/G80A_eZ80').glob('*.vhd'))+[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'fpga/top_ez80.v',r/'fpga/tang20k.sdc',r/'hardware_test/EZ80ALU.COM',r/'sim/tb_alu_r5.sv',r/'sim/tb_arith_corners_r5.sv',r/'sim/build_arith_corners_r5.py']
m=dict(series='restart R5',R4_regression_runs=a['total_fresh_simulation_runs'],preloaded_ALU_COM_runs=b['fresh_runs'],supplemental_arithmetic_runs=c['fresh_runs'],total_fresh_simulation_runs=a['total_fresh_simulation_runs']+b['fresh_runs']+c['fresh_runs'],preloaded_COM_changed=False,COM_sha256=b['COM_sha256'],gowin_tested=False,hardware_tested=False,full_DOS_simulated=False,PC_bits=16,SPS_bits=16,SPL_bits=24,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(r/'verification_result.json').write_text(json.dumps(m,indent=2)+'\n');print('PASS R5 aggregate',m['total_fresh_simulation_runs'],flush=True)
