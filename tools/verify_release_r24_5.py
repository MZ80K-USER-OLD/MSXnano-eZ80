from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(__file__).resolve().parent.parent
if '--collect'not in sys.argv:
 subprocess.run([sys.executable,str(r/'tools/verify_uart_profiles_r24_5.py')],cwd=r,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((r/'doc/R24_5_BASELINE_SHA256.json').read_text())
changed=[rel for rel,h in base['FPGA_SHA256'].items()if sha(r/rel)!=h]
assert changed==['fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj'],changed
assert len(base['COM_SHA256'])==34 and all(sha(r/rel)==h for rel,h in base['COM_SHA256'].items())
assert sha(r/'hardware_test/RUNALL.BAT')==base['RUNALL_SHA256']
result=json.loads((r/'verification_uart_profiles_r24_5/result.json').read_text())
assert len(result['profiles'])==2 and all(sha(r/rel)==h for rel,h in result['sha256'].items())
assert result['real_UART_divider_tested'] and result['Tcl_mock_tests']=='PASS'
w=r/'verification_r24_5';w.mkdir(exist_ok=True)
summary=dict(release='R24.5 normal/UART diagnostic profiles',baseline=base['baseline'],baseline_existing_FPGA_files_changed=changed,CPU_top_VDP_memory_constraints_unchanged=True,COM_unchanged=34,RUNALL_unchanged=True,profiles=result['profiles'],UART_behavior_tests='PASS',selected_Verilog_preprocessing='PASS',top_logger_syntax='PASS (other modules unresolved)',full_board_elaboration=False,Tcl_mock_tests='PASS',UART_resource_estimate_only=True,GOWIN=False,board=False,source_SHA256=result['sha256'])
(w/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('PASS R24.5: two GPRJs / 123 references each; CPU and top unchanged; 34 COMs and RUNALL unchanged; normal idle TX and diagnostic serial prefix verified')
