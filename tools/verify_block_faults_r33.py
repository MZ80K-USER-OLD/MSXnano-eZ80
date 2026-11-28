from pathlib import Path
import os,subprocess,json
R=Path(__file__).resolve().parents[1];W=R/'verification_block_faults_r33';W.mkdir(exist_ok=True)
# The header is generated from the unchanged actual EZ80BLK COM label file.
m=json.loads((R/'hardware_test/EZ80BLK.json').read_text())
(W/'EZ80BLK.vh').write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in m['labels'].items())+f"`define P2_COM_END 16'h{0xff+(R/'hardware_test/EZ80BLK.COM').stat().st_size:04x}\n")
rows=[]
for kind in [0,1]:
 v=W/f'fault{kind}.vvp'
 c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-I',str(W),'-DTEST_HEADER="EZ80BLK.vh"','-DTEST_HEX="hardware_test/EZ80BLK.hex"','-s','tb_block_faults_r33',f'-Ptb_block_faults_r33.KIND={kind}','-o',str(v),str(R/'sim/tb_block_faults_r33.sv'),str(R/'sim/tb_differential_r33.sv'),str(R/'verification/cpu_diag.v'),str(R/'verification/cpu_reference.v'),str(R/'sim/sdram_model33.sv'),str(R/'fpga/src/ez80_memory_bridge.v'),str(R/'fpga/src/memory_ez80.v')]
 a=subprocess.run(c,cwd=R,capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],cwd=R,capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr
 (W/f'fault{kind}.log').write_text(out)
 assert a.returncode!=0 and 'R33/R32 register/flag mismatch'in out,out
 rows.append(dict(kind=kind,fault='boundary disabled'if kind==0 else'zero detection disabled',expected_failure_detected=True))
 print('PASS expected-failure detection',rows[-1]['fault'],flush=True)
(W/'result.json').write_text(json.dumps(rows,indent=2)+'\n')
