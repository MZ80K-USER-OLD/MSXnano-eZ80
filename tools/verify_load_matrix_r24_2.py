from pathlib import Path
import os,subprocess,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_load_matrix_r24_2';w.mkdir(exist_ok=True)
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']]if os.environ.get('IVL_ROOT')else[]);rows=[]
for stress in [0,1]:
 p=w/f'stress{stress}.vvp';a=subprocess.run(iv+['-g2012','-s','tb_load_matrix_r24_2',f'-Ptb_load_matrix_r24_2.STRESS={stress}','-o',str(p),str(r/'sim/tb_load_matrix_r24_2.sv'),str(r/'verification/cpu_1.v')],cwd=r,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([os.environ.get('VVP','vvp'),str(p)],cwd=r,capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;p.with_suffix('.log').write_text(out);assert not a.returncode and 'PASS load_matrix_r24_2 cases=68'in out,out
 print(out.strip(),flush=True);rows.append(dict(stress=stress,cases=68,output=out))
(w/'result.json').write_text(json.dumps(dict(cases=136,profiles=rows,flags_preserved=True,SP_SPS_and_SPL_separate=True,short_upper_rules_preserved=True,all_four_widths=True,source='immediate/absolute/IX-IY displacement',GOWIN=False,board=False,rtl_sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
