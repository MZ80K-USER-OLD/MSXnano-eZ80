from pathlib import Path
import re,os,subprocess,concurrent.futures,json
r=Path(__file__).resolve().parent.parent;root=r.parents[1];w=r/'verification_reg24_trace';w.mkdir(exist_ok=True)
reference=Path(os.environ.get('R24_REFERENCE',str(root/'r24-work/MSXnano_T80_eZ80_restart_R24/verification/cpu_1.v')))
if not reference.is_file():reference=r/'verification_reg24_diff/reference_build/cpu_1.v'
assert reference.is_file(),'Run verify_reg24_differential.py first to build the bundled R24 reference, or set R24_REFERENCE'
s=reference.read_text();at=s.index('module G80A_eZ80');end=s.index('endmodule',at)
monitor='''
 always @(posedge CLK_n) if(RESET_n && reset_s && u0.clken && u0.upper_port_we && u0.upper_port_index!==u0.regaddra)
 $display("ADDR_SPLIT op=%02h page=%h xy=%h dl=%h sl=%h mc=%h ts=%h upper=%h readA=%h WEH=%h WEL=%h events=%02h",u0.ir,u0.iset,u0.xy_state,u0.data_long,u0.stream_long,u0.mcycle,u0.tstate,u0.upper_port_index,u0.regaddra,u0.regweh,u0.regwel,u0.upper_port_events);
'''
(w/'traced_r24.v').write_text(s[:end]+monitor+s[end:])
iv=[os.environ.get('IVERILOG','iverilog')]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
def run(name):
 v=w/(name+'.vvp');args=iv+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s','tb_'+name,f'-Ptb_{name}.PHASE=7','-o',str(v),str(r/'sim'/('tb_'+name+'.sv')),str(w/'traced_r24.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 a=subprocess.run(args,cwd=r,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([os.environ.get('VVP','vvp'),str(v)],cwd=r,capture_output=True,text=True,timeout=1800);out=a.stdout+a.stderr;v.with_suffix('.log').write_text(out);assert not a.returncode and 'PASS '+name in out,out[-1500:]
 rows=sorted(set(x for x in out.splitlines()if x.startswith('ADDR_SPLIT')));print(name,*rows,sep='\n',flush=True);return dict(test=name,observations=rows)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(run,['data_r3','mem_r4','alu_r5','blk_r6','lea_r8']))
(w/'result.json').write_text(json.dumps(dict(reference='R24',tests=rows,scope='Only observed cases in these five suites; not an exhaustive ISA proof'),indent=2)+'\n')
