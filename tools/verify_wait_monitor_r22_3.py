"""Observation-only WAIT monitor, real bridge fault injection, and scoped top wiring.
The scoped elaboration ignores unrelated/vendor modules; it is not full FPGA synthesis.
"""
from pathlib import Path
import subprocess,os,json,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parent.parent;loc=r.parents[1]
w=r/'verification_wait_r22_3';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG',str(loc/'local-iverilog/usr/bin/iverilog'))
vvp=os.environ.get('VVP',str(loc/'local-iverilog/usr/bin/vvp'))
base=[iv,'-B',os.environ.get('IVL_ROOT',str(loc/'local-iverilog/usr/lib/x86_64-linux-gnu/ivl'))]
def run(args,name):
 p=subprocess.run(args,cwd=r,capture_output=True,text=True,timeout=120)
 (w/name).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout+p.stderr
 return p.stdout+p.stderr
src=['fpga/src/ez80_memory_bridge.v','fpga/src/ez80_wait_monitor.v']
run(base+['-g2012','-s','tb_wait_monitor_r22_3','-o',str(w/'unit.vvp'),str(r/'sim/tb_wait_monitor_r22_3.sv')]+[str(r/s)for s in src],'unit_compile.log')
out=run([vvp,str(w/'unit.vvp')],'unit.log');assert 'PASS wait monitor R22.3' in out
run(base+['-g2012','-i','-s','top','-o',str(w/'top_scoped.vvp'),str(r/'fpga/top_ez80.v')]+[str(r/s)for s in src+['fpga/src/memory_ez80.v','fpga/src/ez80_trace_mux.v']],'top_scoped.log')
g=r/'fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj';files=ET.parse(g).findall('.//File')
missing=[n.attrib['path']for n in files if n.attrib.get('enable')=='1' and not(g.parent/n.attrib['path']).is_file()]
assert not missing,missing
assert sum(n.attrib['path']=='../src/ez80_wait_monitor.v' for n in files)==1
(w/'result.json').write_text(json.dumps(dict(unit_and_bridge_fault_injection=True,LED_pages=16,scoped_top_elaboration=True,unrelated_and_vendor_modules_ignored=True,project_paths_checked=len(files),GOWIN=False,hardware=False),indent=2)+'\n')
print(out,end='');print('PASS scoped top wiring and GPRJ paths')
