from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parents[1];w=r/'verification_regression_r25';w.mkdir(exist_ok=True)
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']]if os.environ.get('IVL_ROOT')else[]);vvp=os.environ.get('VVP','vvp')
def cmd(c):
 p=subprocess.run(c,cwd=r,capture_output=True,text=True,timeout=900);assert p.returncode==0,p.stdout[-5000:]+p.stderr[-5000:];return p.stdout+p.stderr
for stem,version in [('ldh',16),('ldx',17)]:cmd(['python3',str(r/f'sim/build_{stem}_unit_r{version}.py'),'--irq'])
cases=[(n,dict(CPU_DIV=4,PHASE=3),None)for n in ['data_r3','mem_r4','alu_r5','blk_r6','lea_r8','control_r10']]
cases += [('control_r10',dict(CPU_DIV=4,PHASE=3,PAUSE_ENABLE=1),None)]
for stem,ver in [('ldh',16),('ldx',17)]:cases.append((f'{stem}_unit_r{ver}',dict(CPU_DIV=4,PHASE=3,PAUSE=1,IRQ_STRESS=2),(stem,ver)))
def run(q):
 name,params,unit=q;top='tb_'+name;label=name+'_'+'_'.join(f'{k}{v}'for k,v in params.items());v=w/(label+'.vvp')
 c=iv+['-g2012','-I',str(r/'sim'),'-I',str(r/'hardware_test'),'-s',top,'-o',str(v)]+[f'-P{top}.{k}={v}'for k,v in params.items()]
 if unit:
  stem,ver=unit;c+=['-DTEST_HEADER="test_irq.vh"','-I',str(r/f'sim/{stem}_r{ver}')]
 c += [str(r/'sim'/(top+'.sv')),str(r/'verification/cpu_1.v')]
 if not unit:c += [str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 cmd(c);out=cmd([vvp,str(v)]);(w/(label+'.log')).write_text(out);assert 'PASS '+name in out,out
 print('PASS regression',label,flush=True);return dict(test=name,parameters=params,log=label+'.log')
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,cases))
(w/'result.json').write_text(json.dumps({'tests':rows,'GOWIN':False,'board':False},indent=2)+'\n')
