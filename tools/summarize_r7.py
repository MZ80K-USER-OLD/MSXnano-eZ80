from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
previous=r/'verification_regression_R6_on_R7.json'
if not previous.exists():
 j=json.loads((r/'verification_result.json').read_text());assert j['series']=='restart R6'
 previous.write_text(json.dumps(j,indent=2)+'\n')
a=json.loads(previous.read_text());b=json.loads((r/'verification_mul_r7_result.json').read_text());c=json.loads((r/'verification_mul_corners_r7_result.json').read_text())
for path,h in a['sha256'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==h,path
paths=list((r/'fpga/G80A_eZ80').glob('*.vhd'))+[r/'fpga/src/ez80_memory_bridge.v',r/'fpga/src/memory_ez80.v',r/'fpga/top_ez80.v',r/'fpga/tang20k.sdc',r/'hardware_test/EZ80MUL.COM',r/'sim/tb_mul_r7.sv',r/'sim/tb_mul_corners_r7.sv',r/'sim/build_mul_corners_r7.py',r/'sim/mul_corners/EZ80M7.COM',r/'sim/mul_corners/vectors.json',r/'tools/verify_mul_r7.py',r/'tools/verify_mul_corners_r7.py',r/'tools/verify_scope_r7.py']
m=dict(series='restart R7',R6_regression_runs=a['total_fresh_simulation_runs'],preloaded_MUL_COM_runs=b['fresh_runs'],supplemental_MLT_runs=c['fresh_runs'],expected_failure_runs=a['expected_failure_runs'],total_fresh_simulation_runs=a['total_fresh_simulation_runs']+b['fresh_runs']+c['fresh_runs'],preloaded_COM_changed=False,COM_sha256=b['COM_sha256'],gowin_tested=False,hardware_tested=False,full_DOS_simulated=False,PC_bits=16,SPS_bits=16,SPL_bits=24,MLT_bits='8x8 -> 16; upper preserved',DSP_mapping='syn_dspstyle=dsp; physical allocation unverified',R6_hardware_user_report={'GOWIN':True,'EZ80BLK_P1_PASS':True,'SofaRun_Space_Manbow_play':True,'LUT_percent':82},sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(r/'verification_result.json').write_text(json.dumps(m,indent=2)+'\n');print('PASS R7 aggregate',m['total_fresh_simulation_runs'],'plus expected failures',m['expected_failure_runs'],flush=True)
