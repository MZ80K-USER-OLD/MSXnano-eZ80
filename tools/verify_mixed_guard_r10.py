from pathlib import Path
import subprocess,os,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_mixed_guard_r10';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=120)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
cases=[(1,1,n) for n in [8,9,10,13,14,15,16,19]]
for adl,stress,guard in cases:
 label=f'a{adl}_s{stress}_g{guard}';p=w/(label+'.vvp')
 run(base+['-g2012','-s','tb_mixed_guard_r10','-o',str(p),f'-Ptb_mixed_guard_r10.TARGET_ADL={adl}',f'-Ptb_mixed_guard_r10.STRESS={stress}',f'-Ptb_mixed_guard_r10.GUARD={guard}',str(r/'sim/tb_mixed_guard_r10.sv'),str(r/'verification/cpu_1.v')])
 out=run([vvp,str(p)]);assert 'PASS '+('pc_r9' if guard<0 else 'mixed_guard_r10') in out,out
 (w/(label+'.log')).write_text(out);print('PASS PC unit',label,flush=True)
(r/'verification_mixed_guard_r10_result.json').write_text(json.dumps(dict(fresh_runs=len(cases),cases=cases,mock_full_address_ROM=True,mixed_suffix_guard_cases=8,prefixes=[64,73,82,91],instruction_classes=["CALL","RET","RST"],native_ADL_IM0_implemented=False,R18_retired_canonical_RST_guards=[16,19],replacement_RST_guards='ADL-source SIS RST08 and LIS RST10' ),indent=2)+'\n')
