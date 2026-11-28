from pathlib import Path
import os,subprocess,json,re
R=Path(__file__).resolve().parents[1];W=R/'verification_input_capture_r36';W.mkdir(exist_ok=True)
rows=[]
for name,candidate,golden in [('normal','cpu_1.v','cpu_reference_normal.v'),('diagnostic','cpu_diag.v','cpu_reference.v')]:
 v=W/(name+'.vvp')
 cmd=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_input_capture_r36',f'-Ptb_input_capture_r36.DIAGNOSTIC_PROFILE={int(name=="diagnostic")}','-o',str(v),str(R/'sim/tb_input_capture_r36.sv'),str(R/'verification'/candidate),str(R/'verification'/golden)]
 a=subprocess.run(cmd,cwd=R,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],cwd=R,capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr
 (W/(name+'.log')).write_text(out);assert not a.returncode and 'PASS R36 input capture'in out,out
 m=re.search(r'checks=(\d+) captures=(\d+) holds=(\d+) mode_bit_ones=(\d+)',out);assert m
 rows.append(dict(profile=name,checks=int(m[1]),captures=int(m[2]),holds=int(m[3]),mode_bit_ones=int(m[4]),cutpoint=True))
 assert int(m[3])==56 and int(m[4])>0
 print(name,out.strip(),flush=True)
(W/'result.json').write_text(json.dumps(dict(rows=rows,forced_source_selectors=True,captured_data_not_forced=True,hardware=False,timing=False),indent=2)+'\n')
