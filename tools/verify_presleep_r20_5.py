from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_presleep_r20_5';w.mkdir(exist_ok=True);rows=[]
for fault,run in [(0,1),(1,1),(0,0)]:
 label=f'f{fault}_run{run}';v=w/(label+'.vvp')
 cmd=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-I',str(r/'hardware_test'),'-DTEST_HEADER="EZ80SP0.vh"','-DTEST_HEX="hardware_test/EZ80SP0.hex"','-DEXPECTED_SLEEPS=1','-s','tb_presleep_r20_5','-o',str(v),f'-Ptb_presleep_r20_5.FAULT={fault}',f'-Ptb_presleep_r20_5.RUN_REQUEST={run}']+[str(r/n)for n in ['sim/tb_presleep_r20_5.sv','verification/cpu_diag.v','fpga/tn_vdp_v3_v9958/src/pinfilter.v','sim/sdram_model33.sv','fpga/src/memory_ez80.v','fpga/src/ez80_memory_bridge.v']]
 a=subprocess.run(cmd,capture_output=True,text=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],cwd=r,capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 expected='READY (use /RUN)'if not run else'FAIL stage 0'if fault else'PASS'
 assert a.returncode==0 and 'EZ80SP0 R20.3 PRE-SLP: '+expected in out,out
 if fault:assert 'ADDR=0A6004 EXP=3E ACT=3F'in out,out
 rows.append(dict(fault=fault,run=run,output=out));print('PASS pre-SLP',fault,run,flush=True)
(r/'verification_presleep_r20_5_result.json').write_text(json.dumps(dict(fresh_runs=len(rows),cases=rows,physical_failure_reproduced=False),indent=2)+'\n')
