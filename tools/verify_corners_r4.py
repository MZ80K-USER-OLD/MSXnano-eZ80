from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_corners_r4';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=300)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
run(['python3','sim/build_corners_r4.py'])
for phase in (0,7):
 p=w/f'phase{phase}.vvp'
 run(base+['-g2012','-I',str(r/'sim/corners'),'-s','tb_corners_r4','-o',str(p),f'-Ptb_corners_r4.PHASE={phase}']+[str(r/'sim/tb_corners_r4.sv'),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')])
 # Fixture readmemh path is shared; provide the internal program at its test input path.
 # It is not the preloaded public EZ80MEM and does not replace it.
 out=run([vvp,str(p)])
 assert 'EZ80C4 R4: PASS' in out and 'PASS corners_r4' in out,out
 (w/f'phase{phase}.log').write_text(out);print('PASS corners_r4',phase,flush=True)
(r/'verification_corners_r4_result.json').write_text(json.dumps({'runs':2,'long_EX_cases_per_run':12,'short_EX_cases_per_run':6,'byte_suffix_cases_per_run':3,'flag_preservation_checked':True,'SPS_SPL_independence_checked':True},indent=2)+'\n')
