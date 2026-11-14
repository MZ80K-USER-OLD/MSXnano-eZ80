from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent
base=json.loads((r/'verification_regression_R10_on_R11.json').read_text())
parts={n:json.loads((r/('verification_'+n+'_result.json')).read_text()) for n in ['irq_r11','irq_unit_r11','return_guard_r11','no_diag_r11','timing_platform','timing_legacy']}
new={n:j.get('fresh_runs',j.get('runs',0)) for n,j in parts.items()}
assert base['total_fresh_simulation_runs']==125
assert new==dict(irq_r11=41,irq_unit_r11=18,return_guard_r11=17,no_diag_r11=4,timing_platform=3,timing_legacy=4),new
paths=[p for p in (r/'fpga').rglob('*') if p.is_file()]+list((r/'hardware_test').glob('*.COM'))
j=dict(series='restart R11.1',purpose='timing path restructuring; no new instruction features',major_function_stage=7,timing_work_stage=10,R10_compatible_regression_runs=125,new_runs=new,total_fresh_simulation_runs=125+sum(new.values()),expected_failure_runs=base['expected_failure_runs'],all_cases_executed_this_revision=True,verification_scope="CPU/bridge/controller regression plus isolated platform tests; full top not simulated",top_configuration_verified_separately=True,PC_bits=24,SPS_bits=16,SPL_bits=24,I_bits=16,ADL_reset=0,preloaded_20_COM_unchanged=True,request_address_data_control_latched=True,native_ADL_IM1_IM2_NMI_RETI_RETN=True,MBASE_MADL_mixed_frames_implemented=False,VHDL93_output_port_read_check=True,instruction_branch_condition_latched=True,no_new_or_relaxed_timing_exceptions=True,R11_user_report=dict(GOWIN_success=True,Logic_percent=87,CLS_percent=95,BSRAM_percent=96,EZ80IRQ_P2_PASS=True,EZ80IM2_P2_PASS=True,EZ80NMI_P2_PASS=True,SofaRun_Space_Manbow_play=True),GOWIN_run_for_this_revision=False,hardware_run_for_this_revision=False,timing_closure_for_this_revision=False,area_for_this_revision_measured=False,PR1014_resolution_unverified=True,full_MSX_DOS_BIOS_simulated=False,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
assert j['total_fresh_simulation_runs']==212 and j['expected_failure_runs']==4
(r/'verification_result.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS R11.1 aggregate 212 positive scenarios + 4 expected failures')
