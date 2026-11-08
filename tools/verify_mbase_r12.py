from pathlib import Path
import subprocess,json,os,concurrent.futures,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_mbase_r12';w.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'sim/build_mbase_r12.py')],check=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[(c,d,s,p,0) for c in range(3) for d,s,p in ([(4,0,0)] if os.environ.get('SMOKE') else [(4,0,0),(4,1,3),(16,1,11)])]+[(0,4,0,0,1),(0,4,0,0,2)]
def run(q):
 c,d,s,p,f=q;label=f'c{c}_d{d}_s{s}_p{p}_f{f}';outp=w/(label+'.vvp')
 a=subprocess.run(base+['-g2012','-I',str(r/'sim'),'-s','tb_mbase_r12','-o',str(outp)]+[f'-Ptb_mbase_r12.{k}={v}' for k,v in dict(CASE=c,CPU_DIV=d,STRESS=s,PHASE=p,FAULT=f).items()]+[str(r/'sim/tb_mbase_r12.sv'),str(r/'verification/cpu_1.v')],text=True,capture_output=True);assert a.returncode==0,a.stderr
 a=subprocess.run([vvp,str(outp)],text=True,capture_output=True,timeout=600);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 if f:assert a.returncode!=0 and ('MBASE state' if f==1 else 'MSX isolation') in out,out
 else:assert a.returncode==0 and 'PASS mbase_r12' in out,out
 print('PASS mbase',q,flush=True);return dict(case=q,result=out[-500:])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
j=dict(fresh_runs=sum(q[-1]==0 for q in cases),expected_failure_runs=2,cases=rows,transfer_values=256,flags_values=256,Z80_NOP=True,short_LIS_SIS_SIL_LIL_addressing=True,ADL_and_Z80_IM1_IM2_NMI_with_nonzero_MBASE=True,SPS_wrap=True,MSX16_isolation=True,flat_24bit_RAM_not_board_mapping=True,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')})
(r/'verification_mbase_r12_result.json').write_text(json.dumps(j,indent=2)+'\n')
