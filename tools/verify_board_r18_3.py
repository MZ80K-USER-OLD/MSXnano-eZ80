from pathlib import Path
import os,subprocess,concurrent.futures,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_board_r18_3';w.mkdir(exist_ok=True)
iv=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT']]
jobs=[('data',15,7,0),('control',15,7,1)]
def run(q):
 kind,div,phase,pause=q;top='tb_data_r3' if kind=='data' else 'tb_control_r10'
 label=f'{kind}_d{div}_p{phase}_pause{pause}';v=w/(label+'.vvp')
 args=iv+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s',top,'-o',str(v),f'-P{top}.CPU_DIV={div}',f'-P{top}.PHASE={phase}']
 if kind=='control':args += [f'-P{top}.PAUSE_ENABLE={pause}']
 args += [str(r/'sim'/(top+'.sv')),str(r/'verification/cpu_1.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 a=subprocess.run(args,cwd=r,text=True,capture_output=True);assert a.returncode==0,a.stderr
 a=subprocess.run([os.environ['VVP'],str(v)],cwd=r,text=True,capture_output=True,timeout=1800)
 out=a.stdout+a.stderr;(w/(label+'.log')).write_text(out)
 expected='EZ80D3 R3: PASS' if kind=='data' else 'EZ80CTL R10: PASS'
 assert a.returncode==0 and expected in out,out[-3000:]
 print('PASS board regression',q,flush=True);return {'case':q,'output':out}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,jobs))
(r/'verification_board_r18_3_result.json').write_text(json.dumps({'fresh_runs':len(rows),'cases':rows,'actual_COM_bytes':True,'full_MSX_DOS_emulation':False,'GOWIN_run':False,'hardware_run':False},indent=2)+'\n')
