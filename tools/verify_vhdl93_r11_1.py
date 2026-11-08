from pathlib import Path
import subprocess,os,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_vhdl93';w.mkdir(exist_ok=True);log=''
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 p=subprocess.run([os.environ.get('GHDL','ghdl'),'-a','--std=93','-fsynopsys',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=w,text=True,capture_output=True);log+=p.stdout+p.stderr;assert p.returncode==0,log
(w/'analysis.log').write_text(log+'PASS fork VHDL-93 analysis\n')
(r/'verification_vhdl93_result.json').write_text(json.dumps(dict(files_analyzed=6,VHDL_standard=1993,output_read_errors=0,GOWIN_run=False),indent=2)+'\n');print('PASS VHDL-93 output-port read restrictions')
