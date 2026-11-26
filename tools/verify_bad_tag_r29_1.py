"""Mechanism test only: inject a bad mode-byte tag into exact R29.
This does not claim to reproduce the physical timing fault on the user's board.
"""
from pathlib import Path
import os,subprocess,json,concurrent.futures
r=Path(__file__).resolve().parents[1];w=r/'verification_bad_tag_r29_1';w.mkdir(exist_ok=True)
s=(r/'sim/tb_compat_com_r26.sv').read_text().replace('tb_compat_com_r26','tb_bad_tag_r29').replace('G80A_eZ80 cpu','G80A_eZ80_reference cpu')
s=s.replace('    initial begin\n        for(i=0;', '''    initial force cpu.di_frame_valid_reg=1'b0;
    always @(posedge c54) if(reset_n && cpu.u0.frame_state==3'b111) begin
      if(cpu.u0.di_reg!==8'h02 && cpu.u0.di_reg!==8'h03)$fatal(1,"fault without valid input byte");
      if(output_text.len()!=0)$fatal(1,"unexpected text before modeled freeze");
      $display("PASS modeled bad tag: DI=%h tag=%b frame_fault=1 no_text=1 (not a board timing reproduction)",cpu.u0.di_reg,cpu.di_frame_valid_reg);
      $finish;
    end
    initial begin
        for(i=0;''',1)
p=w/'tb_bad_tag_r29.sv';p.write_text(s)
def run(n):
 m=json.loads((r/'hardware_test'/(n+'.json')).read_text());blob=r/'hardware_test'/(n+'.COM')
 (w/(n+'.vh')).write_text(''.join(f"`define P2_{k} 16'h{v:04x}\n"for k,v in m['labels'].items())+f"`define P2_COM_END 16'h{255+blob.stat().st_size:04x}\n")
 c=[os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-I',str(w),f'-DTEST_HEADER="{n}.vh"',f'-DTEST_HEX="hardware_test/{n}.hex"','-s','tb_bad_tag_r29','-Ptb_bad_tag_r29.CPU_DIV=4','-Ptb_bad_tag_r29.PHASE=3','-Ptb_bad_tag_r29.PAUSE_ENABLE=1','-o',str(w/(n+'.vvp')),str(p),str(r/'verification/cpu_reference.v'),str(r/'sim/sdram_model33.sv'),str(r/'fpga/src/ez80_memory_bridge.v'),str(r/'fpga/src/memory_ez80.v')]
 a=subprocess.run(c,cwd=r,capture_output=True,text=True);assert not a.returncode,a.stderr
 a=subprocess.run([os.environ['VVP'],str(w/(n+'.vvp'))],cwd=r,capture_output=True,text=True,timeout=600);out=a.stdout+a.stderr;(w/(n+'.log')).write_text(out);assert not a.returncode and 'PASS modeled bad tag'in out,out[-1000:]
 print(n,out[-180:],flush=True);return dict(COM=n,passed=True,injected=True,board_reproduction=False,log=n+'.log')
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(run,['EZ80MIX','EZ80MAD']))
(w/'result.json').write_text(json.dumps(dict(tests=rows,meaning='bad-tag failure mechanism only',board_timing_cause_proven=False),indent=2)+'\n')
