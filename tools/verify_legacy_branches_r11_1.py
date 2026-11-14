from pathlib import Path
import subprocess,os,json,itertools,re
r=Path(__file__).resolve().parent.parent;w=r/'verification_timing_legacy';w.mkdir(exist_ok=True)
code=bytearray([0x31,0,0xf0]);checks=0
for bits in range(16):
 f=sum(((bits>>i)&1)<<b for i,b in enumerate([0,2,6,7]))
 for cc in range(8):
  for kind in ('JP','CALL','RET'):
   code.extend([1,f,0xa5,0xc5,0xf1])
   if kind=='JP':
    dest=0x100+len(code)+4;code.extend([0xc2+cc*8,dest&255,dest>>8,0x14])
   elif kind=='CALL':code.extend([0xc4+cc*8,0xc0,0])
   else:code.extend([0xcd,0x80+cc*4,0])
   checks+=1
 for op in [0x20,0x28,0x30,0x38]:
  code.extend([1,f,0xa5,0xc5,0xf1,op,1,0x14]);checks+=1
code.append(0x76)
s=(r/'sim/tb_locked_r1.vhd').read_text().replace('tb_locked_r1','tb_locked_branches_r11_1')
start=s.index(' function makecode');end=s.index(' constant code:',start)
s=s[:start]+' function makecode return bytes_t is begin return ('+','.join(f'x"{x:02X}"' for x in code)+');end;\n'+s[end:]
needle='m(2):=x"01";';routines=''
for cc in range(8):
 for i,v in enumerate([0xc0+cc*8,0x14,0xc9]):routines+=f'm({0x80+cc*4+i}):=x"{v:02X}";'
routines+='m(192):=x"3C";m(193):=x"C9";'
s=s.replace(needle,needle+routines).replace('wait for 10 ms','wait for 200 ms')
s=s.replace('PASS locked boot profile:',f'PASS {checks} legacy conditional branches:')
(r/'sim/tb_locked_branches_r11_1.vhd').write_text(s)
g=os.environ.get('GHDL','ghdl')
def run(args):
 p=subprocess.run(args,cwd=w,text=True,capture_output=True,timeout=180);assert p.returncode==0,p.stdout+p.stderr;return p.stdout+p.stderr
for folder,suffix in [('G80A',''),('G80A_eZ80','_ez80')]:
 for n in ('t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a'):run([g,'-a','--std=08','-fsynopsys',str(r/'fpga'/folder/(n+suffix+'.vhd'))])
run([g,'-a','--std=08','-fsynopsys',str(r/'sim/tb_locked_branches_r11_1.vhd')])
for ext,wait in itertools.product(('false','true'),repeat=2):
 out=run([g,'-r','--std=08','-fsynopsys','tb_locked_branches_r11_1','-gEXTENSIONS='+ext,'-gINSERT_WAIT='+wait,'--assert-level=error']);assert 'PASS '+str(checks)+' legacy' in out;print('PASS legacy branch comparison',ext,wait,flush=True);(w/f'e{ext}_w{wait}.log').write_text(out)
(r/'verification_timing_legacy_result.json').write_text(json.dumps(dict(fresh_runs=4,branch_operations_per_run=checks,all_16_combinations_of_SZPC=True,original_T80_cycle_comparison=True),indent=2)+'\n')
