from pathlib import Path
import json,os,subprocess,re
R=Path(__file__).resolve().parents[1];W=R/'verification_ir_com_negative_r37';W.mkdir(exist_ok=True)
m=json.loads((R/'hardware_test/EZ80IRF.json').read_text());hdr=W/'EZ80IRF.vh';b=R/'hardware_test/EZ80IRF.COM'
hdr.write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n" for k,v in m['labels'].items())+f"`define P2_COM_END 16'h{0xff+b.stat().st_size:04x}\n")
v=W/'old.vvp';cmd=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-DIRF_TEST','-I',str(W),'-DTEST_HEADER="EZ80IRF.vh"','-DTEST_HEX="hardware_test/EZ80IRF.hex"','-s','tb_com_r37','-Ptb_com_r37.CPU_DIV=4','-o',str(v),str(R/'sim/tb_com_r37.sv'),str(R/'verification/cpu_r36_diag.v'),str(R/'sim/sdram_model33.sv'),str(R/'fpga/src/ez80_memory_bridge.v'),str(R/'fpga/src/memory_ez80.v')]
a=subprocess.run(cmd,cwd=R,capture_output=True,text=True);assert not a.returncode,a.stderr
a=subprocess.run([os.environ['VVP'],str(v)],cwd=R,capture_output=True,text=True,timeout=600);s=a.stdout+a.stderr;(W/'old_r36_expected_fail.log').write_text(s)
assert a.returncode and 'EZ80IRF R37: FAIL' in s and 'EXP A=00 F=40 ACT A=00 F=D2' in s and re.search(r'wrong COM status 0*2 expected 0*1',s),s
(W/'result.json').write_text(json.dumps(dict(original_R36_expected_failure=True,expected_F='40',actual_F='D2',new_COM_detects_old_bug=True),indent=2)+'\n');print('PASS negative: original R36 exposes LD A,I flag defect with EZ80IRF')
