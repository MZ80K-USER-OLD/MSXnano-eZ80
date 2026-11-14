from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_flow_r10';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=120)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
run(['python3','sim/build_flow_r10.py'])
cases=[(0,0),(1,0),(1,3),(1,11)]
for stress,phase in cases:
 label=f's{stress}_p{phase}';p=w/(label+'.vvp')
 run(base+['-g2012','-I',str(r/'sim'),'-s','tb_flow_r10','-o',str(p),f'-Ptb_flow_r10.STRESS={stress}',f'-Ptb_flow_r10.PHASE={phase}',str(r/'sim/tb_flow_r10.sv'),str(r/'verification/cpu_1.v')])
 out=run([vvp,str(p)]);assert 'PASS flow_r10' in out,out
 (w/(label+'.log')).write_text(out);print(out,flush=True)
for fault in (1,2):
 p=w/f'fault{fault}.vvp'
 run(base+['-g2012','-I',str(r/'sim'),'-s','tb_flow_r10','-o',str(p),f'-Ptb_flow_r10.FAULT={fault}',str(r/'sim/tb_flow_r10.sv'),str(r/'verification/cpu_1.v')])
 q=subprocess.run([vvp,str(p)],cwd=r,text=True,capture_output=True,timeout=120)
 assert q.returncode!=0 and 'stack read' in q.stdout,q.stdout+q.stderr
 (w/f'fault{fault}.log').write_text(q.stdout+q.stderr);print('PASS expected failure flow stack fault',fault,flush=True)
(r/'verification_flow_r10_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),expected_failure_runs=2,cases=cases,oracle='sim/flow_r10/oracle.json',mock_full_address_RAM=True),indent=2)+'\n')
