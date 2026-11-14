from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_lea_corners_r8';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=1800)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
run(['python3','sim/build_lea_corners_r8.py'])
cases=[(0,0,0),(7,1,0),(3,0,1),(11,7,1)]
for phase,wait,pause in cases:
 label=f'p{phase}_w{wait}_pause{pause}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'sim/lea_corners'),'-s','tb_lea_corners_r8','-o',str(p)]+[f'-Ptb_lea_corners_r8.{k}={v}' for k,v in dict(PHASE=phase,WAIT_PROFILE=wait,PAUSE_ENABLE=pause).items()]+
 [str(r/'sim/tb_lea_corners_r8.sv'),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(p)])
 assert 'EZ80L8 R8: PASS' in out and 'PASS lea_corners_r8' in out,out
 (w/(label+'.log')).write_text(out);print('PASS lea_corners_r8',label,flush=True)
(r/'verification_lea_corners_r8_result.json').write_text(json.dumps({'fresh_runs':len(cases),'cases':cases,'EA_cases_per_run':72,'LEA_cases_per_run':57,'PEA_cases_per_run':15,'IRQs_per_run':2,'PEA_write_cycles_per_run':37,'reference':'independent signed displacement, stack bytes/order/wrap, full AF, short/long and source preservation; IRQ at transaction boundary; WAIT and CEN hold'},indent=2)+'\n')
