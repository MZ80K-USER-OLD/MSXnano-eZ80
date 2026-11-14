from pathlib import Path
import subprocess,os,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_pc_r9';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=120)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
cases=[(adl,stress,-1) for adl in (0,1) for stress in (0,1)]
for adl,stress,guard in cases:
 label=f'a{adl}_s{stress}_g{guard}';p=w/(label+'.vvp')
 run(base+['-g2012','-s','tb_pc_r9','-o',str(p),f'-Ptb_pc_r9.TARGET_ADL={adl}',f'-Ptb_pc_r9.STRESS={stress}',f'-Ptb_pc_r9.GUARD={guard}',str(r/'sim/tb_pc_r9.sv'),str(r/'verification/cpu_1.v')])
 out=run([vvp,str(p)]);assert 'PASS '+('pc_r9' if guard<0 else 'guard_r9') in out,out
 (w/(label+'.log')).write_text(out);print('PASS PC unit',label,flush=True)
(r/'verification_pc_r9_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),cases=cases,wrap_modes=[16,24],mock_full_address_ROM=True,ADL_control_guard_cases=0,retired_stage6_guards=[0,1,2,3,4,5],retired_stage7_guards=[6,7],ADL_IRQ_implemented=False),indent=2)+'\n')
