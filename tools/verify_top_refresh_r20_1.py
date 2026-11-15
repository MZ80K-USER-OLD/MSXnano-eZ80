from pathlib import Path
import os,subprocess,json,re
r=Path(__file__).resolve().parent.parent;w=r/'verification_top_refresh_r20_1';w.mkdir(exist_ok=True)
s=(r/'fpga/top_ez80.v').read_text();assert '.CPU_Sleep(cpu_sleep_state),.Sleep_Timer(sleep_timer)'in s and '.cpu_sleep(cpu_sleep_state),.sleep_timer(sleep_timer)'in s and 'memory_ctrl_ez80 #(.SLEEP_REFRESH(1))'in s
# GHDL's emitted core is specialized, so remove only that instance's generic
# overrides in this simulation copy. All unrelated modules remain blackboxes.
a=s.index('    G80A_eZ80 #(');b=s.index('    ) cpu1 (',a);s=s[:a]+'    G80A_eZ80 cpu1 ('+s[b+len('    ) cpu1 ('):];(w/'top_specialized.v').write_text(s)
a=subprocess.run([os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-i','-s','top','-o',str(w/'top.vvp'),str(w/'top_specialized.v'),str(r/'verification/cpu_diag.v'),str(r/'fpga/src/memory_ez80.v'),str(r/'fpga/src/ez80_memory_bridge.v')],capture_output=True,text=True);(w/'elaboration.log').write_text(a.stdout+a.stderr);assert a.returncode==0,a.stdout+a.stderr
(r/'verification_top_refresh_r20_1_result.json').write_text(json.dumps(dict(fresh_runs=1,CPU_memory_bridge_ports_elaborated=True,unrelated_modules_blackboxed=True,GOWIN_run=False,full_system_simulated=False),indent=2)+'\n');print('PASS top refresh wiring and partial elaboration')
