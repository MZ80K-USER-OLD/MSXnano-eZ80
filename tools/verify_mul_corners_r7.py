from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_mul_corners_r7';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=600)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
run(['python3','sim/build_mul_corners_r7.py'])
cases=[(0,0,0),(7,1,0),(3,0,1),(11,1,1)]
for phase,wait,pause in cases:
 label=f'p{phase}_w{wait}_pause{pause}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'sim/mul_corners'),'-s','tb_mul_corners_r7','-o',str(p)]+[f'-Ptb_mul_corners_r7.{k}={v}' for k,v in dict(PHASE=phase,FETCH_WAIT=wait,PAUSE_ENABLE=pause,INTERNAL_WAIT=int(wait or pause)).items()]+
 [str(r/'sim/tb_mul_corners_r7.sv'),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 out=run([vvp,str(p)])
 assert 'EZ80M7 R7: PASS' in out and 'PASS mul_corners_r7' in out,out
 (w/(label+'.log')).write_text(out);print('PASS mul_corners_r7',label,flush=True)
(r/'verification_mul_corners_r7_result.json').write_text(json.dumps({'fresh_runs':len(cases),'cases':cases,'MLT_cases_per_run':71,'locked_NEG_alias_cases':4,'IRQs_per_run':1,'reference':'independent unsigned 8x8 integer products; full AF and upper-byte preservation; all prefixes and both register banks; SPS/SPL selection'},indent=2)+'\n')
