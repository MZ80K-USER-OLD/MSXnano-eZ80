from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;loc=r.parents[1];w=r/'verification_io_removed_r23_1';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'));ivl=os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'));vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
def run(q):
 s,e=q;v=w/f's{s}_e{e}.vvp';top='tb_io_removed_r23_1'
 a=subprocess.run([iv,'-B',ivl,'-g2012','-s',top,'-o',str(v),f'-P{top}.STRESS={s}',f'-P{top}.EVENT={e}',str(r/'sim/tb_io_removed_r23_1.sv'),str(r/'verification/cpu_1.v')],capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([vvp,str(v)],capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr;v.with_suffix('.log').write_text(out);assert not a.returncode and 'PASS removed IO'in out,out
 print(out.strip(),flush=True);return dict(profile=q,output=out)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,[(0,0),(1,0)]))
(w/'result.json').write_text(json.dumps(dict(cases=160,profiles=rows,GOWIN=False,hardware=False),indent=2)+'\n')
