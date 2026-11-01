from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_arith_corners_r5';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=600)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
run(['python3','sim/build_arith_corners_r5.py'])
cases=[(0,0,0),(7,1,0),(3,0,1),(11,1,1)]
for phase,wait,pause in cases:
 label=f'p{phase}_w{wait}_pause{pause}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'sim/arith_corners'),'-s','tb_arith_corners_r5','-o',str(p)]+[f'-Ptb_arith_corners_r5.{k}={v}' for k,v in dict(PHASE=phase,FETCH_WAIT=wait,PAUSE_ENABLE=pause).items()]+
 [str(r/'sim/tb_arith_corners_r5.sv'),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(p)])
 assert 'EZ80A5 R5: PASS' in out and 'PASS arith_corners_r5' in out,out
 (w/(label+'.log')).write_text(out);print('PASS arith_corners_r5',label,flush=True)
(r/'verification_arith_corners_r5_result.json').write_text(json.dumps({'fresh_runs':len(cases),'cases':cases,'long_arithmetic_cases_per_run':56,'short_arithmetic_cases_per_run':8,'cases_per_run':64,'reference':'independent integer operations; H from bit11/borrow into12; XY ignored'},indent=2)+'\n')
