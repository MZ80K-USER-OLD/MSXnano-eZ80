from pathlib import Path
import os,subprocess,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_no_diag_r11';w.mkdir(exist_ok=True)
# Explicit source CPU choice; copy into cpu_r10 for a self-contained reproducible bundle.
cpu=Path(os.environ.get('R10_CPU_VERILOG',str(r/'verification')))
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
rows=[]
for f in sorted((r/'hardware_test').glob('*.json')):
 if f.stem not in ('EZ80IRQ','EZ80IM2','EZ80NMI','EZ80RST'):continue
 meta=json.loads(f.read_text());name=meta['name']
 for request,ext,stress in ((1,1,1),):
  p=w/f'{name}_r{request}_e{ext}.vvp'
  args=base+['-g2012','-I',str(r/'hardware_test'),f'-DTEST_HEADER="{name}.vh"',f'-DTEST_HEX="hardware_test/{name}.hex"','-s','tb_no_diag_r11','-o',str(p),f'-Ptb_no_diag_r11.REQUEST={request}',f'-Ptb_no_diag_r11.EXTENDED={ext}',f'-Ptb_no_diag_r11.STRESS={stress}',str(r/'sim/tb_no_diag_r11.sv'),str(cpu/f'cpu_{ext}.v')]
  q=subprocess.run(args,cwd=r,capture_output=True,text=True,timeout=60);assert q.returncode==0,q.stdout+q.stderr
  q=subprocess.run([vvp,str(p)],cwd=r,capture_output=True,text=True,timeout=120);assert q.returncode==0,q.stdout+q.stderr
  expected='READY' if not request else 'NOT READY' if ext else 'UNSUPPORTED'
  assert name+' P2: '+expected in q.stdout and 'PASS R10 guard' in q.stdout,q.stdout
  (w/(p.stem+'.log')).write_text(q.stdout+q.stderr);rows.append(dict(name=name,COM_sha256=meta['sha256'],request=request,extended=ext,stress=stress,expected=expected));print('PASS no diagnostics',name,expected,flush=True)
(r/'verification_no_diag_r11_result.json').write_text(json.dumps(dict(runs=len(rows),RTL_scope='R11 DIAGNOSTICS=false: hook-dependent programs reject before ADL',cases=rows,cpu_verilog_sha256={str(e):hashlib.sha256((cpu/f'cpu_{e}.v').read_bytes()).hexdigest() for e in (0,1)}),indent=2)+'\n')
