from pathlib import Path
import os,subprocess,json
R=Path(__file__).resolve().parents[1];W=R/'verification_frame_gate_r36';W.mkdir(exist_ok=True)
v=W/'gate.vvp'
a=subprocess.run([os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_frame_gate_r36','-o',str(v),str(R/'sim/tb_frame_gate_r36.sv'),str(R/'verification/cpu_1.v')],capture_output=True,text=True);assert not a.returncode,a.stderr
a=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr;(W/'gate.log').write_text(out);assert not a.returncode and 'PASS R36 frame-gate cases=512' in out,out
(W/'result.json').write_text(json.dumps(dict(cases=512,frame_idle_bytes=256,IM0_NOP_bypass_bytes=256,normal_instruction_execution_held=True,cutpoint=True,full_CPU=False),indent=2)+'\n');print(out.strip())
