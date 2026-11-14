from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
m=json.loads((r/'verification_result_v34_1.json').read_text())
guard=json.loads((r/'verification_guard_v34_1.json').read_text());sel=json.loads((r/'verification_selected_v34_1.json').read_text())
assert sel['passed']==129 and not sel['failed'] and guard['compatibility_cases']==16 and guard['bios_cases']==1
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in m['source_sha256'].items():assert sha(r/name)==h,name
m.update(fresh_simulation_runs=151,com_cases=5,locked_compatibility_cases=16,selected_cpu_cases=129,bios_initial_cases=1,
 full_bios_boot_verified=False,v34_black_screen_root_cause_confirmed=False,v34_1_hardware_boot_verified=False)
paths=[r/'sim/tb_guard_compat341.vhd',r/'sim/tb_bios_compare341.vhd',r/'tools/run_guard341.py',r/'tools/run_selected341.py',r/'tools/regression_cases_v34_1_selected.json']
m['test_source_sha256'].update({str(p.relative_to(r)):sha(p) for p in paths})
(r/'verification_result_v34_1.json').write_text(json.dumps(m,indent=2)+'\n')
print('Collected 151 current simulation runs; full BIOS boot/Gowin/hardware unverified')
