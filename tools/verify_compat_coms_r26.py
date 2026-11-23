from pathlib import Path
import subprocess,os,json,concurrent.futures,hashlib
r=Path(__file__).resolve().parents[1];w=r/'verification_compat_coms_r26';w.mkdir(exist_ok=True)
names=['EZ80D3','EZ80ALU','EZ80BLK','EZ80MUL','EZ80LEA','EZ80F9','EZ80ADL','EZ80CTL','EZ80I16','EZ80IM2','EZ80IRQ','EZ80LDH','EZ80LDX','EZ80NMI','EZ80RST','EZ80TST','EZ80NP6','EZ80ION','EZ80DEC','EZ80MAD','EZ80MIX','EZ80MB']
if os.environ.get('NAMES'):names=os.environ['NAMES'].split(',')
def run(name):
 m=json.loads((r/'hardware_test'/(name+'.json')).read_text());hdr=w/(name+'.vh');blob=r/'hardware_test'/(name+'.COM')
 hdr.write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in m['labels'].items())+f"`define P2_COM_END 16'h{0xff+blob.stat().st_size:04x}\n")
 v=w/(name+'.vvp');c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-I',str(w),f'-DTEST_HEADER="{name}.vh"',f'-DTEST_HEX="hardware_test/{name}.hex"','-s','tb_compat_com_r26','-o',str(v),str(r/'sim/tb_compat_com_r26.sv'),str(r/'verification/cpu_diag.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 p=subprocess.run(c,cwd=r,capture_output=True,text=True)
 if p.returncode:out=p.stderr
 else:
  try:p=subprocess.run([os.environ['VVP'],str(v)],cwd=r,capture_output=True,text=True,timeout=240);out=p.stdout+p.stderr
  except subprocess.TimeoutExpired:out='TIMEOUT';p.returncode=1
 (w/(name+'.log')).write_text(out)
 ok=not p.returncode and 'PASS compat_com_r26'in out
 print('PASS'if ok else'FAIL',name,out[-600:]if not ok else'',flush=True)
 return dict(COM=name,passed=ok,sha256=hashlib.sha256(blob.read_bytes()).hexdigest(),log=name+'.log')
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:rows=list(pool.map(run,names))
(w/('result_'+('_'.join(names) if os.environ.get('NAMES') else 'all')+'.json')).write_text(json.dumps(dict(cases=rows,actual_COM=True,actual_SDRAM_RTL=True,BDOS_EI=True,board=False),indent=2)+'\n')
assert all(x['passed']for x in rows),[x['COM']for x in rows if not x['passed']]
