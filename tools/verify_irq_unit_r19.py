from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_irq_unit_r19';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=120)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
run(['python3','sim/build_irq_unit_r11.py']);rows=[]
for case in range(6):
 for stress,phase in ([(0,0)] if os.environ.get('SMOKE') else [(0,0),(1,3),(1,11)]):
  label=f'c{case}_s{stress}_p{phase}';p=w/(label+'.vvp')
  run(base+['-g2012','-I',str(r/'sim'),'-s','tb_irq_unit_r19','-o',str(p)]+[f'-Ptb_irq_unit_r19.{k}={v}' for k,v in dict(CASE=case,STRESS=stress,PHASE=phase).items()]+[str(r/'sim/tb_irq_unit_r19.sv'),str(r/'verification/cpu_1.v')])
  out=run([vvp,str(p)]);assert 'PASS irq_unit_r11' in out,out;(w/(label+'.log')).write_text(out);rows.append((case,stress,phase));print(out,flush=True)
(r/'verification_irq_unit_r19_result.json').write_text(json.dumps(dict(fresh_runs=len(rows),cases=rows,flat_24bit_RAM=True,not_board_memory_map=True),indent=2)+'\n')
