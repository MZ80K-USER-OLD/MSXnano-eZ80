from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;loc=r.parents[1];w=r/'verification_bridge_r23_3';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'));ivl=os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'));vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
rows=[]
for qual,pred in [(0,0),(1,0),(0,1),(1,1)]:
    top='tb_bridge_r23_3';v=w/f'q{qual}_p{pred}.vvp'
    a=subprocess.run([iv,'-B',ivl,'-g2012','-s',top,'-o',str(v),f'-P{top}.QUALIFIED={qual}',f'-P{top}.PREDECODED={pred}',str(r/'sim/tb_bridge_r23_3.sv'),str(r/'fpga/src/ez80_memory_bridge.v')],capture_output=True,text=True);assert not a.returncode,a.stderr
    a=subprocess.run([vvp,str(v)],capture_output=True,text=True,timeout=180);out=a.stdout+a.stderr;v.with_suffix('.log').write_text(out);assert not a.returncode and 'PASS bridge33 10240'in out,out
    rows.append(dict(qualified=qual,predecoded=pred,checks=10240,output=out));print('PASS bridge',qual,pred,flush=True)
(w/'result.json').write_text(json.dumps(dict(profiles=rows,checks=40960,GOWIN=False,hardware=False),indent=2)+'\n')

top='tb_bridge_capture_r23_3';v=w/'capture.vvp'
a=subprocess.run([iv,'-B',ivl,'-g2012','-s',top,'-o',str(v),str(r/'sim/tb_bridge_capture_r23_3.sv'),str(r/'fpga/src/ez80_memory_bridge.v')],capture_output=True,text=True);assert not a.returncode,a.stderr
a=subprocess.run([vvp,str(v)],capture_output=True,text=True,timeout=180);out=a.stdout+a.stderr;v.with_suffix('.log').write_text(out);assert not a.returncode and 'PASS capture phases cases=48'in out,out
p=w/'result.json';j=json.loads(p.read_text());j['capture_phase_cases']=48;j['idle_clocks']=4096;j['drain_cancel_reset_checked']=True;p.write_text(json.dumps(j,indent=2)+'\n');print(out.strip(),flush=True)
