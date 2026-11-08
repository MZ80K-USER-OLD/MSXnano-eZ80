from pathlib import Path
import os,subprocess,json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_slot_r11_4';w.mkdir(exist_ok=True)
iv=os.environ.get('IVERILOG','iverilog');base=[iv]+(['-B',os.environ['IVL_ROOT']] if os.environ.get('IVL_ROOT') else [])
for fault in (5,6):
 target=w/f'leak{fault}.vvp';args=base+['-g2012','-I',str(r/'hardware_test'),'-I',str(r/'sim'),'-s','tb_mem_r4',f'-Ptb_mem_r4.FAULT={fault}','-Ptb_mem_r4.CPU_DIV=4','-o',str(target)]+[str(r/n) for n in ['sim/tb_mem_r4.sv','verification/cpu_1.v','sim/sdram_model33.sv','fpga/src/ez80_memory_bridge.v','fpga/src/memory_ez80.v']]
 p=subprocess.run(args,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
 p=subprocess.run([os.environ.get('VVP','vvp'),str(target)],cwd=r,capture_output=True,text=True,timeout=300);out=p.stdout+p.stderr;target.with_suffix('.log').write_text(out)
 assert p.returncode!=0 and ('secondary slot '+('write' if fault==5 else 'read')+' detected CPU=07ffff MSX=ffff MREQ_n=0') in out,out
s=(r/'fpga/top_ez80.v').read_text();a=s.index('    //expanded slot 3');b=s.index('    // slots decoding',a);assert (r/'sim/secondary_slot_r11_4.vh').read_text()==s[a:b]
j=dict(expected_failure_runs=2,actual_top_slot_logic_extracted=True,expanded_primary_slot_forced_selected=True,upper_bank_not_used_by_slot_decoder=True,address_07FFFF_alias_injection_detected=True,ideal_RTL_test_only=True,hardware_leak_not_excluded=True)
(r/'verification_slot_r11_4_result.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS expected slot-alias injection detected; actual top slot logic audited')
