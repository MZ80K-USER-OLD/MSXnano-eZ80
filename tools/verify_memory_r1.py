from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_memory';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(args,timeout=240):
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr
bridge=str(r/'fpga/src/ez80_memory_bridge.v');mem=str(r/'fpga/src/memory_ez80.v');old=str(r/'fpga/src/memory.v');model=str(r/'sim/sdram_model33.sv')
cases=[('tb_bridge33',{},[bridge])]
cases += [('tb_memory33',dict(PHASE=i),[model,bridge,mem]) for i in range(16)]
cases += [('tb_memory_compat33',dict(PHASE=i),[old,mem]) for i in range(4)]
cases += [('tb_capture_r1',dict(PHASE=i),[old,mem]) for i in range(4)]
cases += [('tb_memory33',dict(SKIP_INIT=0),[model,bridge,mem])]
for i,(tb,params,files) in enumerate(cases):
 dest=w/f'case{i}.vvp'
 run(base+['-g2012','-s',tb,'-o',str(dest)]+[f'-P{tb}.{k}={v}' for k,v in params.items()]+[str(r/'sim'/(tb+'.sv'))]+files)
 out=run([vvp,str(dest)])
 assert 'PASS ' in out and 'FATAL' not in out,out
 (w/f'case{i}.log').write_text(out);print('PASS memory',i,tb,params,flush=True)
# Negative control: reconstruct the former live-data mux in a temporary source.
prior=Path(mem).read_text().replace('ext_data_latched : sdram_din_latched','ext_data_latched : mapper_din')
(w/'live_data_reference.v').write_text(prior)
run(base+['-g2012','-s','tb_capture_r1','-o',str(w/'negative.vvp'),str(r/'sim/tb_capture_r1.sv'),old,str(w/'live_data_reference.v')])
p=subprocess.run([vvp,str(w/'negative.vvp')],cwd=r,text=True,capture_output=True)
assert p.returncode!=0 and 'live upstream data reached SDRAM' in p.stdout,p.stdout+p.stderr
(w/'negative.log').write_text('EXPECTED FAILURE of former live-data mux\n'+p.stdout+p.stderr)
print('PASS negative control rejects former live-data mux',flush=True)
(r/'verification_memory_result.json').write_text(json.dumps({'fresh_runs':len(cases),'bridge_decode_runs':1,'SDRAM_functional_runs':16,'legacy_pin_comparison_runs':4,'payload_hold_runs':4,'power_on_runs':1,'negative_control_runs':1,'gowin_tested':False},indent=2)+'\n')
