from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_return_guard_r11';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[(a,s,o,0) for a in (0,1) for s in (0x40,0x49,0x52,0x5b) for o in (0x45,0x4d)]+[(1,0,0x75,1)]
for a,s,o,alias in cases:
 label=f'a{a}_s{s:02x}_o{o:02x}_x{alias}';p=w/(label+'.vvp')
 args=base+['-g2012','-s','tb_return_guard_r11','-o',str(p)]+[f'-Ptb_return_guard_r11.{k}={v}' for k,v in dict(ADL=a,SUFFIX=s,OP=o,ALIAS=alias).items()]+[str(r/'sim/tb_return_guard_r11.sv'),str(r/'verification/cpu_1.v')]
 q=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=60);assert q.returncode==0,q.stdout+q.stderr
 q=subprocess.run([vvp,str(p)],cwd=r,text=True,capture_output=True,timeout=60);assert q.returncode==0,q.stdout+q.stderr
 (w/(label+'.log')).write_text(q.stdout+q.stderr);print('PASS return guard',label,flush=True)
(r/'verification_return_guard_r11_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),cases=cases),indent=2)+'\n')
