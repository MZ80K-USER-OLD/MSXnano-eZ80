from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parents[1];w=r/'verification_window_irq_r26';w.mkdir(exist_ok=True);rows=[]
for pair in [(n,l)for n in(0,1)for l in(0,1)]:
 nmi,lock=pair
 for stress in (0,1):
  v=w/f'n{nmi}s{stress}l{lock}.vvp';c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_window_irq_r26',f'-Ptb_window_irq_r26.NMI={nmi}',f'-Ptb_window_irq_r26.LOCK={lock}',f'-Ptb_window_irq_r26.STRESS={stress}','-o',str(v),str(r/'sim/tb_window_irq_r26.sv'),str(r/'verification/cpu_1.v')]
  p=subprocess.run(c,capture_output=True,text=True);assert not p.returncode,p.stderr
  p=subprocess.run([os.environ['VVP'],str(v)],capture_output=True,text=True,timeout=60);out=p.stdout+p.stderr;v.with_suffix('.log').write_text(out)
  assert not p.returncode and 'PASS window_irq R26'in out,out
  print(out.strip(),flush=True);rows.append(dict(NMI=nmi,stress=stress,lock=lock,output=out))
(w/'result.json').write_text(json.dumps(dict(cases=rows,separate_MSX_and_extended_arrays=True,physical_SDRAM=False),indent=2)+'\n')
