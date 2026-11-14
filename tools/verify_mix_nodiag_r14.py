from pathlib import Path
import os,subprocess,json,hashlib,shutil
r=Path(__file__).resolve().parent.parent;w=r/'verification_mix_nodiag_r14';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');vvp=os.environ.get('VVP','vvp');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
shutil.copyfile(r/'verification/cpu_1.v',w/'cpu.v')
cmd=base+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-DTEST_HEADER="EZ80MIX.vh"','-DTEST_HEX="hardware_test/EZ80MIX.hex"','-s','tb_irq_r11','-Ptb_irq_r11.SUPPORTED=1','-o',str(w/'run.vvp'),str(r/'sim/tb_irq_r11.sv'),str(w/'cpu.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
a=subprocess.run(cmd,cwd=r,capture_output=True,text=True);assert a.returncode==0,a.stderr
a=subprocess.run([vvp,str(w/'run.vvp')],cwd=r,capture_output=True,text=True,timeout=1800);out=a.stdout+a.stderr;(w/'run.log').write_text(out)
assert a.returncode==0 and 'EZ80MIX P2: PASS' in out and 'PASS irq_r11' in out,out
(r/'verification_mix_nodiag_r14_result.json').write_text(json.dumps(dict(fresh_runs=1,expected_failure_runs=0,COM='EZ80MIX.COM',DIAGNOSTICS=False,actual_CPU_bridge_SDRAM=True,output=out,sha256={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'fpga/G80A_eZ80').glob('*.vhd')}),indent=2)+'\n')
print('PASS MIX actual COM with diagnostic injection disabled')
