from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parent.parent;w=r/'verification_im0_r19';w.mkdir(exist_ok=True)
iv=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT']]
ops=os.environ.get('OPS');jobs=[(c,s,15 if s else 4) for c in range(3) for s in (0,1)]
def run(q):
 c,s,d=q;label=f'c{c}_s{s}_d{d}';v=w/(label+'.vvp')
 args=iv+['-g2012','-s','tb_im0_r19','-o',str(v),f'-Ptb_im0_r19.CTX={c}',f'-Ptb_im0_r19.STRESS={s}',f'-Ptb_im0_r19.CPU_DIV={d}',str(r/'sim/tb_im0_r19.sv'),str(r/'verification/cpu_1.v')]
 a=subprocess.run(args,capture_output=True,text=True);assert a.returncode==0,a.stderr
 selected=ops.split(',') if ops else [None]
 for op in selected:
  a=subprocess.run([os.environ['VVP'],str(v)]+(['+OP='+op] if op else []),capture_output=True,text=True,timeout=1800)
  out=a.stdout+a.stderr;(w/(label+('_op'+op if op else '')+'.log')).write_text(out)
  assert a.returncode==0 and 'PASS IM0 matrix cases=' in out,out[-3500:]
 print('PASS IM0 profile',q,flush=True)
 return {'profile':q,'opcode_count':len(selected) if ops else 256}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,jobs))
(r/('verification_im0_r19_smoke_result.json' if ops else 'verification_im0_r19_result.json')).write_text(json.dumps({'fresh_runs':sum(x['opcode_count'] for x in rows),'profiles':rows,'external_IACK':True,'flat_24bit_RAM':True,'CPU_CEN_WAIT_BUSRQ':True,'not_board_timing':True},indent=2)+'\n')
