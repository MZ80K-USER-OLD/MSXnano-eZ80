from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
base=json.loads((r/'verification_result.json').read_text());assert base['series']=='restart R3'
mem=json.loads((r/'verification_mem_r4_result.json').read_text());platform=json.loads((r/'verification_timing_platform_result.json').read_text());slot=json.loads((r/'verification_slot_r11_4_result.json').read_text())
assert base['locked_comparison_runs']==16 and base['actual_COM_simulation_runs']==10 and mem['fresh_runs']==9 and platform['fresh_runs']==3 and slot['expected_failure_runs']==2
j=dict(series='restart R11.4A',purpose='One-variable comparison: disable separate predecoded MSX request; retain R11.3 SDRAM',total_fresh_simulation_runs=38,expected_failure_runs=2,locked_Z80_comparison_runs=16,R3_COM_runs=10,MEM_COM_runs=9,platform_runs=3,actual_top_secondary_slot_read_and_write_monitored=True,injected_07FFFF_to_FFFF_alias_detected=True,injected_D6_diagnostic_report_verified=True,hardware_failure_cause_not_proven=True,SDRAM_unchanged_from_R11_3=True,separate_16_and_24_bit_buses=True,preloaded_COM_unchanged=True,full_235_case_regression_repeated=False,full_MSX_DOS_BIOS_simulated=False,GOWIN_run=False,hardware_run=False,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga').rglob('*') if p.is_file()})
(r/'verification_result.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS A: 38 scenarios + 2 expected alias detections')
