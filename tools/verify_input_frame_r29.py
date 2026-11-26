from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parents[1];w=r/'verification_input_frame_r29';w.mkdir(exist_ok=True);v=w/'run.vvp'
c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_input_frame_r29','-o',str(v),str(r/'sim/tb_input_frame_r29.sv'),str(r/'verification/cpu_diag.v')]
p=subprocess.run(c,cwd=r,capture_output=True,text=True);assert not p.returncode,p.stderr
p=subprocess.run([os.environ['VVP'],str(v)],cwd=r,capture_output=True,text=True,timeout=120);out=p.stdout+p.stderr;(w/'result.log').write_text(out);assert not p.returncode and 'PASS R29 input/frame'in out,out
(w/'result.json').write_text(json.dumps(dict(checks=8192,captures=2048,holds=6144,all_bytes=256,sources=['raw','diagnostic port E7E7','diagnostic port E6','diagnostic IACK'],WAIT=[0,1],forced_unit=True,CPU_execution=False,output=out),indent=2)+'\n');print(out)
