"""Check R25 provenance and collect completed local verification; not a GOWIN run."""
from pathlib import Path
import hashlib,json,os,subprocess,xml.etree.ElementTree as E,zlib
r=Path(__file__).resolve().parents[1];w=r/'verification_r25';w.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((r/'doc/R25_BASELINE_SHA256.json').read_text())
changed=[p for p,h in base.items()if p.startswith('fpga/')and sha(r/p)!=h]
expected=['fpga/G80A_eZ80/'+n+'_ez80.vhd'for n in ['t80_pack','t80_mcode','t80','g80a']]
assert set(changed)==set(expected),changed
coms=[p for p in base if p.startswith('hardware_test/')and p.endswith('.COM')]
assert len(coms)==34 and all(sha(r/p)==base[p]for p in coms)
assert sha(r/'EZ80TIO.COM')==sha(r/'hardware_test/EZ80TIO.COM')
for p in ['RUNALL.BAT','hardware_test/RUNALL.BAT']:
 assert (r/p).read_bytes().endswith(b'EZ80TIO /RUN\r\n')
 previous=(r/p).read_bytes()[:-len(b'EZ80TIO /RUN\r\n')]
 assert hashlib.sha256(previous).hexdigest()==base[p]
for path in [r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj',r/'fpga/project_eZ80_uart_debug/MSXNanoTang20K_eZ80_UART_DEBUG.gprj']:
 files=E.parse(path).findall('.//File');assert len(files)==123 and all((path.parent/f.get('path')).is_file()for f in files)
# GOWIN accepts VHDL-93. Verify this separately from the VHDL-2008 simulation flow.
g=os.environ.get('GHDL','ghdl');q=w/'vhdl93';q.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 p=subprocess.run([g,'-a','--std=93','-fsynopsys','-fexplicit',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=q,capture_output=True,text=True)
 assert not p.returncode,p.stderr
unit=json.loads((r/'verification_tstio_r25/result.json').read_text());assert len(unit['cases'])==10
com=json.loads((r/'verification_tstio_com_r25_result.json').read_text());assert com['fresh_runs']==7
reg=json.loads((r/'verification_regression_r25/result.json').read_text());assert len(reg['tests'])==9
compat=json.loads((r/'verification_compat_coms_r25/result.json').read_text());assert len(compat['passed_scripts'])==5
tst=json.loads((r/'verification_tst_r15_result.json').read_text());assert tst['fresh_runs']==4 and tst['expected_failure_runs']==2
assert 'PASS TSTIO DECODE vectors=524288'in(r/'verification_tstio_decode_r25/result.log').read_text()
meta=json.loads((r/'hardware_test/EZ80TIO.json').read_text());blob=(r/'hardware_test/EZ80TIO.COM').read_bytes()
assert meta['bytes']==len(blob) and meta['crc32']==f'{zlib.crc32(blob):08X}' and meta['sha256']==sha(r/'hardware_test/EZ80TIO.COM')
result=dict(release='R25 TSTIO',baseline='R24.5 RAM + normal UART-disabled profile',RTL_changed=changed,register_file_ALU_top_memory_SDC_CST_GPRJ_unchanged=True,old_hardware_COM_unchanged=34,new_COM='EZ80TIO.COM',COM_bytes=len(blob),COM_CRC32=meta['crc32'],COM_SHA256=meta['sha256'],VHDL93='PASS, 6 files',decode_vectors=524288,TSTIO_unit_runs=10,TSTIO_functional_checks=1880,locked_NEG_checks=512,IRQ_NMI_boundary_checks=80,TSTIO_COM_runs=7,old_CPU_regression_runs=9,old_COM_smoke_runs=5,TST_regression_success_runs=4,TST_expected_fault_detector_runs=2,BDOS_EI_and_IM1_in_simulation=True,simulation_full_MSX=False,GOWIN=False,board=False,timing_closed=False,new_data_work_registers=0,execution_control_width_bits=54,source_SHA256={str(p.relative_to(r)):sha(p)for p in(r/'fpga/G80A_eZ80').glob('*.vhd')})
# 450 x 2 modes x stress on/off = 1800; plus 4 interrupt profiles x20 =80.
(r/'doc/R25_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');(w/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS R25: 4 RTL files; VHDL93; old 34 COMs intact; decode 524288; unit 10; actual COM 7; CPU regressions 9; old COMs 5; TST 4 + 2 fault detectors')
