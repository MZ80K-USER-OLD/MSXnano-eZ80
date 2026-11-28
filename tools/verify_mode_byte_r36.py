from pathlib import Path
import os,subprocess,json
R=Path(__file__).resolve().parents[1];W=R/'verification_mode_byte_r36';W.mkdir(exist_ok=True)
rows=[]
for fault in [0,1,2]:
 v=W/f'f{fault}.vvp'
 cmd=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_mode_byte_r36',f'-Ptb_mode_byte_r36.FAULT={fault}','-o',str(v),str(R/'sim/tb_mode_byte_r36.sv'),str(R/'verification/cpu_1.v')]
 a=subprocess.run(cmd,cwd=R,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],cwd=R,capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr;(W/f'f{fault}.log').write_text(out)
 if fault:assert a.returncode!=0 and ('saved mode bit mismatch'if fault==1 else'return path mismatch')in out,out
 else:assert not a.returncode and 'PASS R36 mode-bit-only cases=512'in out,out
 rows.append(dict(fault=fault,normal_pass=not fault,expected_failure_detected=bool(fault),scope='forced frame_mode entry; actual captured byte; bit0, return state, SPL/count/address verified'))
 print('PASS mode bit cases=512'if not fault else f'PASS mode expected failure {fault}',flush=True)
(W/'result.json').write_text(json.dumps(dict(cases=512,rows=rows,all_256_bytes=True,both_stream_widths=True,full_CPU=False,timing=False),indent=2)+'\n')
