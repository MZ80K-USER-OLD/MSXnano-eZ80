"""R24 regression runner. --collect packages completed local run receipts only."""
from pathlib import Path
import os,sys,subprocess,json,hashlib,shutil,zlib,datetime,re
r=Path(__file__).resolve().parent.parent;loc=r.parents[1];w=r/'verification_r24';w.mkdir(exist_ok=True)
env=os.environ.copy()
for k,p in dict(GHDL='local-ghdl/usr/bin/ghdl',GHDL_PREFIX='local-ghdl/usr/lib/ghdl/mcode/vhdl',IVERILOG='local-iverilog/usr/bin/iverilog',IVL_ROOT='local-iverilog/usr/lib/x86_64-linux-gnu/ivl',VVP='local-iverilog/usr/bin/vvp').items():
 if (loc/p).exists():env.setdefault(k,str(loc/p))
checks=[
 ('verify_vhdl93_r11_1.py','verification_vhdl93_result.json','verification_vhdl93'),
 ('verify_mcode_r24.py',None,'verification_mcode_r24'),
 ('verify_decode_width_r24.py','verification_decode_width_r24/result.json','verification_decode_width_r24'),
 ('verify_decode_com_r24.py','verification_decode_com_r24_result.json','verification_decode_com_r24'),
 ('verify_mem_r4.py','verification_mem_r4_result.json','verification_mem_r4'),
 ('verify_mr4_r21_3.py','verification_mr4_r21_3/result.json','verification_mr4_r21_3'),
 ('verify_io_nop_com_r23_2.py','verification_io_nop_com_r23_2_result.json','verification_io_nop_com_r23_2'),
 ('verify_mixed_r14.py','verification_mixed_r14_result.json','verification_mixed_r14'),
 ('verify_madl_r13.py','verification_madl_r13_result.json','verification_madl_r13'),
 ('verify_mbase_r12.py','verification_mbase_r12_result.json','verification_mbase_r12'),
 ('verify_ldh_unit_r16.py','verification_ldh_unit_r16_result.json','verification_ldh_unit_r16_final'),
 ('verify_ldx_unit_r17.py','verification_ldx_unit_r17_result.json','verification_ldx_unit_r17_final'),
 ('verify_prefix_com_r19_1.py','verification_prefix_com_r19_1_result.json','verification_prefix_com_r19_1'),
 ('verify_im0_com_r19.py','verification_im0_com_r19_result.json','verification_im0_com_r19'),
 ('verify_alu_r5.py','verification_alu_r5_result.json','verification_alu_r5'),
 ('verify_blk_r6.py','verification_blk_r6_result.json','verification_blk_r6'),
 ('verify_mul_r7.py','verification_mul_r7_result.json','verification_mul_r7'),
 ('verify_lea_r8.py','verification_lea_r8_result.json','verification_lea_r8')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if '--collect' not in sys.argv:
 subprocess.run([sys.executable,str(r/'tools/synthesize_r22.py')],cwd=r,env=env,check=True)
 for name,_,_ in checks:
  e=env.copy();e.pop('CASE_INDEX',None);e.pop('SMOKE',None)
  if name in ('verify_prefix_com_r19_1.py','verify_im0_com_r19.py'):e['CASE_INDEX']='0,1'
  print('Running',name,flush=True)
  subprocess.run([sys.executable,str(r/'tools'/name)],cwd=r,env=e,check=True)
rtl={str(p.relative_to(r)):sha(p) for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}
assert json.loads((r/'verification/r22_rtl_sha256.json').read_text())==rtl,'Synthesized CPU does not match current RTL'
rows=[]
for name,result,logs in checks:
 d=json.loads((r/result).read_text()) if result else dict(modes=4,vectors_per_mode=458752,total_vectors=1835008)
 if 'sha256' in d:
  for key,val in d['sha256'].items():assert sha(r/key)==val,(name,key)
 dest=w/'checks'/name.removesuffix('.py');dest.mkdir(parents=True,exist_ok=True)
 if result:shutil.copy2(r/result,dest/'result.json')
 paths=sorted((r/logs).glob('*.log'));assert paths,(name,'missing logs')
 for p in paths:shutil.copy2(p,dest/p.name)
 if name=='verify_mcode_r24.py':
  for i in range(4):assert f'PASS mcode equivalence Mode={i} vectors=458752' in (r/logs/f'mode{i}.log').read_text()
 rows.append(dict(script=name,result=d,log_sha256={p.name:sha(p)for p in paths}))
s=(r/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text()
assert not re.search(r'(?:if|elsif)[^\n]*\b(?:Ext_Active|ADL_Mode|Has_Width)\b',s)
com=r/'hardware_test/EZ80DEC.COM';assert com.read_bytes()==(r/'EZ80DEC.COM').read_bytes()
summary=dict(release='R24',date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline='hardware-confirmed R23.3',GOWIN_run=False,board_run=False,timing_closed=False,checks=rows,rtl_sha256=rtl,cpu_models={p.name:sha(p)for p in (r/'verification').glob('cpu_*.v')},new_COM=dict(name=com.name,bytes=com.stat().st_size,crc32=f'{zlib.crc32(com.read_bytes()):08X}',sha256=sha(com)),limits='Simulation only. Standard opcode/cycle tables remain; static eZ80 qualifiers are registered. GOWIN area and timing require measurement.')
(w/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
print('PASS R24 release checks; GOWIN / physical board not tested')
