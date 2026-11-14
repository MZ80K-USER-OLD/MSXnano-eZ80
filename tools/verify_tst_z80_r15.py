from pathlib import Path
import subprocess,json,os,concurrent.futures,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_tst_z80_r15';w.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'sim/build_tst_r15.py')],check=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
cases=[(4,d,s,p,0) for d,s,p in [(4,0,0),(4,1,3),(16,1,11)]]
def run(q):
 c,d,s,p,f=q;label=f'c{c}_d{d}_s{s}_p{p}_f{f}';outp=w/(label+'.vvp')
 a=subprocess.run(base+['-g2012','-I',str(r/'sim'),'-s','tb_tst_r15','-o',str(outp)]+[f'-Ptb_tst_r15.{k}={v}' for k,v in dict(CASE=c,CPU_DIV=d,STRESS=s,PHASE=p,FAULT=f).items()]+[str(r/'sim/tb_tst_r15.sv'),str(r/'verification/cpu_1.v')],text=True,capture_output=True);assert a.returncode==0,a.stderr
 a=subprocess.run([vvp,str(outp)],text=True,capture_output=True,timeout=1800);out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 if f:assert a.returncode!=0 and 'MBASE state' in out,out
 else:assert a.returncode==0 and 'PASS tst_r15' in out,out
 print('PASS mbase',q,flush=True);return dict(case=q,result=out[-500:])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
j=dict(fresh_runs=sum(q[-1]==0 for q in cases),expected_failure_runs=0,cases=rows,A_values=7,register_sources=7,Z80_mode_with_extensions_enabled=True,immediate=True,memory=True,source_and_A_preserved=True,flags_SZHPNC_and_XY_checked=True,ED74_legacy_NEG=False,locked_ED64_legacy_NEG=False,all_four_width_suffixes=True,WAIT_and_CEN_pause=True,nonzero_MBASE=False,flat_24bit_RAM_not_board_mapping=True,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')})
(r/'verification_tst_z80_r15_result.json').write_text(json.dumps(j,indent=2)+'\n')
