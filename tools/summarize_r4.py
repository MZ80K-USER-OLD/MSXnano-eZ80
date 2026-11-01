from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
previous=r/'verification_regression_R3_on_R4.json'
if not previous.exists():
 p=r/'verification_result.json';j=json.loads(p.read_text())
 assert j['series']=='restart R3'
 previous.write_text(json.dumps(j,indent=2)+'\n')
a=json.loads(previous.read_text());b=json.loads((r/'verification_mem_r4_result.json').read_text());c=json.loads((r/'verification_corners_r4_result.json').read_text())
for path,h in a['sha256'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==h,path
paths=list((r/'fpga/G80A_eZ80').glob('*.vhd'))+[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'fpga/top_ez80.v',r/'fpga/tang20k.sdc',r/'hardware_test/EZ80MEM.COM',r/'sim/tb_mem_r4.sv',r/'sim/tb_corners_r4.sv',r/'sim/build_corners_r4.py']
m=dict(series='restart R4',locked_comparison_runs=a['locked_comparison_runs'],R3_COM_regression_runs=a['actual_COM_simulation_runs'],preloaded_MEM_COM_runs=b['fresh_runs'],supplemental_runs=c['runs'],total_fresh_simulation_runs=a['locked_comparison_runs']+a['actual_COM_simulation_runs']+b['fresh_runs']+c['runs'],preloaded_COM_changed=False,COM_sha256=b['COM_sha256'],gowin_tested=False,hardware_tested=False,full_DOS_simulated=False,PC_bits=16,SPS_bits=16,SPL_bits=24,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(r/'verification_result.json').write_text(json.dumps(m,indent=2)+'\n');print('PASS R4 aggregate',m['total_fresh_simulation_runs'],flush=True)
