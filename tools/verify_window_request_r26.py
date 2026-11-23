from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parents[1];w=r/'verification_window_request_r26';w.mkdir(exist_ok=True);rows=[]
for diag,fault in [(0,0),(1,0),(1,1),(1,2),(1,3)]:
 v=w/f'd{diag}_f{fault}.vvp'
 c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_window_request_r26',f'-Ptb_window_request_r26.DIAGNOSTICS={diag}',f'-Ptb_window_request_r26.FAULT={fault}','-o',str(v),str(r/'sim/tb_window_request_r26.sv'),str(r/'verification'/('cpu_diag.v'if diag else'cpu_1.v')),str(r/'fpga/src/ez80_memory_bridge.v')]
 p=subprocess.run(c,capture_output=True,text=True);assert not p.returncode,p.stderr
 p=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=180);out=p.stdout+p.stderr;v.with_suffix('.log').write_text(out)
 if fault:assert p.returncode!=0 and ('MSX isolation'if fault in(1,2)else'request qualification')in out,out
 else:assert not p.returncode and 'PASS MSX window request R26'in out,out
 rows.append(dict(diagnostics=diag,fault=fault,output=out));print('PASS window request',diag,fault,out[-100:],flush=True)
(w/'result.json').write_text(json.dumps(dict(cases=rows,all_256_MBASE_by_256_banks=True,WAIT_CEN_refresh_IO_IACK=True),indent=2)+'\n')
