from pathlib import Path
import subprocess,os,itertools,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_exsp_work_r11_2';w.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'sim/build_exsp_work_r11_2.py')],check=True)
iv=os.environ.get('IVERILOG','iverilog');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
rows=[]
for pair,nmi,mc in itertools.product(range(3),range(2),[2,5]):
 dest=w/f'p{pair}_n{nmi}_m{mc}.vvp';args=base+['-g2012','-I',str(r/'sim'),'-s','tb_exsp_work_r11_2','-o',str(dest)]+[f'-Ptb_exsp_work_r11_2.{k}={v}' for k,v in dict(PAIR=pair,NMI=nmi,TRIGGER_MC=mc).items()]+[str(r/'sim/tb_exsp_work_r11_2.sv'),str(r/'verification/cpu_1.v')]
 p=subprocess.run(args,text=True,capture_output=True);assert p.returncode==0,p.stderr
 p=subprocess.run([os.environ.get('VVP','vvp'),str(dest)],text=True,capture_output=True,timeout=120);out=p.stdout+p.stderr;(dest.with_suffix('.log')).write_text(out);assert p.returncode==0 and 'PASS EXSP work' in out,out
 print(out,flush=True);rows.append((pair,nmi,mc))
(r/'verification_exsp_work_r11_2_result.json').write_text(json.dumps(dict(fresh_runs=len(rows),cases=rows,HL_IX_IY=True,IRQ_and_NMI_deferred_to_instruction_end=True,read_then_write_order=True,WAIT_and_CEN_holds=True,flags_and_SPL_preserved=True,flat_RAM=True),indent=2)+'\n')
