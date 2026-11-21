from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;loc=r.parents[1];w=r/'verification_decode_width_r24';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'));ivl=os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl') if (loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl').is_dir() else None);vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
rows=[]
for stress in [0,1]:
    top='tb_decode_width_r24';v=w/f'stress{stress}.vvp'
    cmd=[iv]+(['-B',ivl] if ivl else [])+['-g2012','-s',top,'-o',str(v),f'-P{top}.STRESS={stress}',str(r/'sim/tb_decode_width_r24.sv'),str(r/'verification/cpu_1.v')]
    a=subprocess.run(cmd,capture_output=True,text=True);assert not a.returncode,a.stderr
    a=subprocess.run([vvp,str(v)],capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr;v.with_suffix('.log').write_text(out);assert not a.returncode and 'PASS decode width'in out,out
    print(out.strip(),flush=True);rows.append(dict(stress=stress,output=out))
old=Path(os.environ.get('BASELINE_CPU',str(loc/'r23-3-work/MSXnano_T80_eZ80_restart_R23_3/verification/cpu_1.v')))
old_checked=False
if old.is_file():
    v=w/'old_expected_failure.vvp';cmd[-1]=str(old);cmd[cmd.index('-o')+1]=str(v);cmd.insert(-2,'-Ptb_decode_width_r24.CHECK_DESCRIPTOR=0')
    a=subprocess.run(cmd,capture_output=True,text=True);assert not a.returncode,a.stderr
    a=subprocess.run([vvp,str(v)],capture_output=True,text=True,timeout=300);out=a.stdout+a.stderr;v.with_suffix('.log').write_text(out)
    assert a.returncode and 'terminal CB lost width / leaked prefix'in out,out
    old_checked=True;print('PASS baseline exposes terminal-CB width leak',flush=True)
(w/'result.json').write_text(json.dumps(dict(cases=64,profiles=rows,baseline_expected_failure_checked=old_checked,GOWIN=False,hardware=False),indent=2)+'\n')
