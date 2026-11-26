from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parents[1];w=r/'verification_strobes_r28';w.mkdir(exist_ok=True);v=w/'run.vvp'
c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_strobes_r28','-o',str(v),str(r/'sim/tb_strobes_r28.sv'),str(r/'verification/cpu_diag.v'),str(r/'verification/cpu_reference.v')]
p=subprocess.run(c,cwd=r,capture_output=True,text=True);assert not p.returncode,p.stderr
p=subprocess.run([os.environ['VVP'],str(v)],cwd=r,capture_output=True,text=True,timeout=120);out=p.stdout+p.stderr;(w/'result.log').write_text(out);assert not p.returncode and 'PASS R28 strobe matrix'in out,out
(w/'result.json').write_text(json.dumps(dict(combinations=1024,checks=5121,output=out,forced_strobe_unit=True,CPU_execution=False),indent=2)+'\n');print(out)
