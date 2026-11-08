from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
previous=r/'verification_regression_R7_on_R8.json'
if not previous.exists():
 j=json.loads((r/'verification_result.json').read_text());assert j['series']=='restart R7'
 previous.write_text(json.dumps(j,indent=2)+'\n')
a=json.loads(previous.read_text());b=json.loads((r/'verification_lea_r8_result.json').read_text());c=json.loads((r/'verification_lea_corners_r8_result.json').read_text())
for path,h in a['sha256'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==h,path
paths=list((r/'fpga/G80A_eZ80').glob('*.vhd'))+[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'fpga/top_ez80.v',r/'fpga/tang20k.sdc',r/'hardware_test/EZ80LEA.COM',r/'sim/tb_lea_r8.sv',r/'sim/tb_lea_corners_r8.sv',r/'sim/build_lea_corners_r8.py',r/'sim/lea_corners/EZ80L8.COM',r/'sim/lea_corners/vectors.json',r/'sim/lea_corners/case_plan.vh',r/'tools/verify_lea_r8.py',r/'tools/verify_lea_corners_r8.py',r/'tools/verify_scope_r8.py']
m=dict(series='restart R8',R7_regression_runs=a['total_fresh_simulation_runs'],preloaded_LEA_COM_runs=b['fresh_runs'],supplemental_EA_runs=c['fresh_runs'],expected_failure_runs=a['expected_failure_runs'],total_fresh_simulation_runs=a['total_fresh_simulation_runs']+b['fresh_runs']+c['fresh_runs'],preloaded_COM_changed=False,COM_sha256=b['COM_sha256'],gowin_tested=False,hardware_tested=False,full_DOS_simulated=False,PC_bits=16,SPS_bits=16,SPL_bits=24,EA_adder='existing Indexed_Address reused',R7_hardware_user_report={'GOWIN':True,'EZ80MUL_P1_PASS':True,'SofaRun_Space_Manbow_play':True},sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(r/'verification_result.json').write_text(json.dumps(m,indent=2)+'\n');print('PASS R8 aggregate',m['total_fresh_simulation_runs'],'plus expected failures',m['expected_failure_runs'],flush=True)
