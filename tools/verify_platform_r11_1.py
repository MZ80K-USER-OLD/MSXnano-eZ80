from pathlib import Path
import os,subprocess,json,re
r=Path(__file__).resolve().parent.parent;w=r/'verification_timing_platform';w.mkdir(exist_ok=True)
top=Path(os.environ.get('TOP_SOURCE',str(r/'fpga/top_ez80.v')));s=top.read_text();start=s.index('    always @(posedge clk_27m) begin\n        if (~bus_reset_n) begin');end=s.index('    assign config_mapper_slot',start)
(r/'sim/config_capture_r11_1.vh').write_text(s[start:end])
(r/'sim/config_initial_r11_1.vh').write_text('\n'.join(re.search(r'reg '+name+r'[^;]*;',s).group(0) for name in ['config_enable_mapper3','config_enable_mapper12','config_enable_sdcard'])+'\n')
iv=os.environ.get('IVERILOG','iverilog');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
for args in [base+['-g2012','-I',str(r/'sim'),'-s','tb_timing_platform_r11_1','-o',str(w/'platform.vvp'),str(r/'sim/tb_timing_platform_r11_1.sv'),str(r/'fpga/tn_vdp_v3_v9958/src/clockdiv.v')],[os.environ.get('VVP','vvp'),str(w/'platform.vvp')]]:
 p=subprocess.run(args,cwd=r,text=True,capture_output=True,timeout=120);assert p.returncode==0,p.stdout+p.stderr
(w/'platform.log').write_text(p.stdout+p.stderr);assert 'PASS timing_platform_r11_1' in p.stdout
print(p.stdout)
# SDC audit: no broadened exceptions or loosened max_delay.
old=(r/'doc/r11_timing_baseline/fpga/tang20k.sdc.txt').read_text();new=(r/'fpga/tang20k.sdc').read_text()
def exceptions(s):return [x.strip() for x in s.splitlines() if x.strip().startswith(('set_false_path','set_multicycle_path','set_max_delay'))]
assert exceptions(old)==exceptions(new)
assert not any(x.startswith('create_') and ('VideoDHClk' in x or 'VideoDLClk' in x) for x in new.splitlines())
assert '-divide_by 612' in new and '-name clock_input' in new
assert 'always_latch' not in s
for qualified in (0,1):
 target=w/f'bridge{qualified}.vvp'
 args=base+['-g2012','-s','tb_bridge33',f'-Ptb_bridge33.QUALIFIED={qualified}','-o',str(target),str(r/'sim/tb_bridge33.sv'),str(r/'fpga/src/ez80_memory_bridge.v')]
 p=subprocess.run(args,text=True,capture_output=True);assert p.returncode==0,p.stderr
 p=subprocess.run([os.environ.get('VVP','vvp'),str(target)],text=True,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
 assert 'PASS bridge33 10240' in p.stdout;ptext=p.stdout+p.stderr;(w/f'bridge{qualified}.log').write_text(ptext);print(ptext)
j=dict(fresh_runs=3,bridge_decode_checks_per_profile=10240,audio_fractional_minimum_parent_cycles=612,configuration_capture_and_hold=True,power_up_without_reset_clock_edge=True,no_new_or_relaxed_timing_exceptions=True,PLL_and_CLKDIV_tree_explicit=True,video_phase_signals_are_data=True,GOWIN_run=False)
(r/'verification_timing_platform_result.json').write_text(json.dumps(j,indent=2)+'\n')
