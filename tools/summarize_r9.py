from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
previous=r/'verification_regression_R8_on_R9.json'
if not previous.exists():
 j=json.loads((r/'verification_result.json').read_text());assert j['series']=='restart R8'
 previous.write_text(json.dumps(j,indent=2)+'\n')
a=json.loads(previous.read_text());b=json.loads((r/'verification_fetch_r9_result.json').read_text());c=json.loads((r/'verification_pc_r9_result.json').read_text())
for path,h in a['sha256'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==h,path
paths=list((r/'fpga/G80A_eZ80').glob('*.vhd'))+[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'fpga/top_ez80.v',r/'fpga/tang20k.sdc',r/'hardware_test/EZ80F9.COM',r/'hardware_test/build_fetch_r9.py',r/'hardware_test/EZ80F9.json',r/'sim/tb_fetch_r9.sv',r/'sim/fetch_plan.vh',r/'sim/tb_pc_r9.sv',r/'tools/verify_fetch_r9.py',r/'tools/verify_pc_r9.py',r/'tools/verify_scope_r9.py']
m=dict(series='restart R9',major_stage=5,R8_regression_runs=a['total_fresh_simulation_runs'],new_fetch_COM_runs=b['fresh_runs'],PC_unit_runs=c['fresh_runs'],expected_failure_runs=a['expected_failure_runs'],total_fresh_simulation_runs=a['total_fresh_simulation_runs']+b['fresh_runs']+c['fresh_runs'],new_COM='EZ80F9.COM',COM_sha256=b['COM_sha256'],gowin_tested=False,hardware_tested=False,full_DOS_simulated=False,PC_bits=24,SPS_bits=16,SPL_bits=24,ADL_reset=0,JP_scope='unconditional immediate + SIS/LIL transitions',ADL_remaining_control='R10 native stage6 enabled; old six guard tests retired',ADL_interrupts='gated; not implemented until stage7',R8_hardware_user_report={'GOWIN':True,'EZ80LEA_P1_PASS':True,'SofaRun_Space_Manbow_play':True},sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(r/'verification_result.json').write_text(json.dumps(m,indent=2)+'\n');print('PASS R9 aggregate',m['total_fresh_simulation_runs'],'plus expected failures',m['expected_failure_runs'],flush=True)
