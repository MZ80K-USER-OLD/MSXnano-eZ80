"""Execute actual ED57/5F/47/4F instructions; independent flag equations, no CEmu oracle."""
from pathlib import Path
import os,subprocess,sys,json,hashlib,itertools
R=Path(__file__).resolve().parents[1];K=R/'fuse_test';sys.path.insert(0,str(K/'tools'))
from run_fuse import read_raw,FIELDS
from compare import compare_record
W=R/'verification_ir_flags_r37';W.mkdir(exist_ok=True)
cases=[];expected=[]
def append(op,adl,value,iff1,iff2,carry,reverse=False):
 s=dict(zip(FIELDS,[0,0x123456,0x345678,0x56789a,0x9876,0xabcdef,0x654321,0x876543,0x246810,0x135790,0x234560,0x120100 if adl else 0x100,0xab35,0xfe,iff1,iff2,2,0,adl,0x7b,0,0xc100]))
 if reverse:s['AF']=(value<<8)|(0xa5 if carry else 0x5a)
 else:
  s['AF']=0xa500|0xfe|carry
  if op==0x57:s['I']=0xab00|value
  else:s['R']=(value&128)|((value-2)&127)
 pc=s['PC'] if adl else(s['MBASE']<<16)|s['PC'];mem={f'{pc:06x}':0xed,f'{pc+1:06x}':op}
 ident=f'ED{op:02X}_adl{adl}_v{value:02X}_iff{iff1}{iff2}_c{carry}'
 c=dict(id=ident,instruction=f'ED_{op:02X}',coverage='independent_spec',code=[0xed,op],steps=1,io_seed=0x5a,initial=s,memory=mem,mask={k:0xffffff for k in FIELDS})
 e=dict(s);e['PC']+=2;e['R']=(s['R']&128)|((s['R']+2)&127)
 if reverse:
  if op==0x47:e['I']=(s['I']&0xff00)|value
  else:e['R']=value
 else:
  flags=(value&0xa8)|(64 if value==0 else 0)|(iff2<<2)|carry
  e['AF']=(value<<8)|flags
 cases.append(c);expected.append(dict(id=ident,state=e,memory=mem))
for op,adl,value,iff1,iff2,carry in itertools.product([0x57,0x5f],[0,1],range(256),[0,1],[0,1],[0,1]):append(op,adl,value,iff1,iff2,carry)
for op,adl,value,carry in itertools.product([0x47,0x4f],[0,1],range(256),[0,1]):append(op,adl,value,1,0,carry,True)
assert len(cases)==10240
stim=W/'stimulus.txt'
with stim.open('w') as f:
 for i,c in enumerate(cases):
  f.write(f'{i:x} 1 5a 2 2 0\n'+' '.join(f'{c["initial"][k]:x}' for k in FIELDS)+'\n')
  for a,v in c['memory'].items():f.write(f'{a} {v:x}\n')
v=W/'ir.vvp';a=subprocess.run([os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-I',str(K/'build'),'-s','tb_fuse','-o',str(v),str(K/'sim/tb_fuse.sv'),str(K/'build/dut.v')],capture_output=True,text=True);assert not a.returncode,a.stderr
p=subprocess.run([os.environ['VVP'],str(v),'+INPUT='+str(stim),'+OUTPUT='+str(W/'raw.txt')],capture_output=True,text=True,timeout=3600)
(W/'simulation.log').write_text(p.stdout+p.stderr);assert not p.returncode,p.stdout+p.stderr
rows=[]
for d,c,e in itertools.zip_longest(read_raw(W/'raw.txt',cases),cases,expected):
 assert d is not None and c is not None
 row=compare_record(c,e,dict(events=[]),d);rows.append(row)
failed=[r for r in rows if not r['passed']]
result=dict(cases=len(rows),passed=len(rows)-len(failed),failed=len(failed),LD_A_I_R_cases=8192,LD_I_R_A_cases=2048,all_byte_values=True,ADL_both=True,IFF1_IFF2_independent=True,C_both=True,undocumented_XY_from_value=True,full_instruction_execution=True,independent_of_CEmu=True,failures=failed)
(W/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert not failed,failed[:2]
print('PASS R37 IR flags: 10240 independently computed instruction cases')
