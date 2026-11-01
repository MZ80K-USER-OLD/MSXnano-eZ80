from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_block_corners_r6';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=600)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
run(['python3','sim/build_block_corners_r6.py'])
cases=[(0,0,0),(7,1,0),(3,0,1),(11,7,1)]
for phase,wait,pause in cases:
 label=f'p{phase}_w{wait}_pause{pause}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'sim/block_corners'),'-s','tb_block_corners_r6','-o',str(p)]+[f'-Ptb_block_corners_r6.{k}={v}' for k,v in dict(PHASE=phase,WAIT_PROFILE=wait,PAUSE_ENABLE=pause).items()]+
 [str(r/'sim/tb_block_corners_r6.sv'),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(p)])
 assert 'EZ80B6 R6: PASS' in out and 'PASS block_corners_r6' in out,out
 (w/(label+'.log')).write_text(out);print('PASS block_corners_r6',label,flush=True)
for negative,reason in [(1,'IRQ return PC'),(2,'IRQ SPS')]:
 label=f'negative_{negative}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'sim/block_corners'),'-s','tb_block_corners_r6','-o',str(p),f'-Ptb_block_corners_r6.NEGATIVE={negative}']+
 [str(r/'sim/tb_block_corners_r6.sv'),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 q=subprocess.run([vvp,str(p)],cwd=r,text=True,capture_output=True,timeout=600);out=q.stdout+q.stderr
 assert q.returncode!=0 and reason in out,out
 (w/(label+'.log')).write_text(out);print('PASS expected failure',label,flush=True)
(r/'verification_block_corners_r6_result.json').write_text(json.dumps({'fresh_runs':len(cases),'expected_failure_runs':2,'cases':cases,'block_cases_per_run':15,'IRQs_per_run':9,'reference':'independent count/address/flags; byte-boundary IRQ and saved prefix PC; WAIT register hold'},indent=2)+'\n')
