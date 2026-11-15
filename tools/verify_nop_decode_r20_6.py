from pathlib import Path
import os,re,subprocess,json
r=Path(__file__).resolve().parent.parent;w=r/'verification_nop_decode_r20_6';w.mkdir(exist_ok=True)
s=(r/'verification/cpu_1.v').read_text();name=re.search(r'module (t80_mcode[^\s(]+)',s).group(1);a=s.index('module '+name);header=s[a:s.index(');',a)]
ports=re.findall(r'\b(input|output)\s+(\[[^\]]+\]\s*)?(\w+)',header)
declarations='\n'.join(('reg 'if d=='input'else'wire ')+(width or'')+n+('=0;'if d=='input'else';')for d,width,n in ports)
sides=['write','iorq','halt','read_to_reg','read_to_acc','save_alu','call','rstp','jump','setdi','setei','exchangedh','exchangerp','exchangeaf','exchangers','ldz','ldw','ldsphl','i_btr']
tb='module tb_nop_decode_r20_6;\n'+declarations+'\n'+name+' dut('+','.join('.'+n+'('+n+')'for _,_,n in ports)+');\ninteger k;initial begin\n'
tb+='''ir=8'h76;iset=2;mcycle=1;
for(k=0;k<576;k=k+1)begin
 ext_active=k%2;data_long=(k/2)%2;stream_long=(k/4)%2;adl_mode=(k/8)%2;has_width=(k/16)%2;xy_state=(k/32)%3;interrupt_mode=(k/96)%3;f=(k/288)?8'hff:0;
 #1;if(imode!==(ext_active?2'b11:2'b01))$fatal(1,"ED76 changed interrupt mode incorrectly case=%d",k);
'''
tb+='if({'+','.join(sides)+'}!==0||mcycles!==1)$fatal(1,"ED76 has side effects case=%d",k);end\n'
tb+='''iset=0;ext_active=1;has_width=0;xy_state=0;#1;if(halt!==1)$fatal(1,"normal HALT lost");
ext_active=0;#1;if(halt!==1)$fatal(1,"locked HALT lost");
iset=2;ext_active=1;ir=8'h56;#1;if(imode!==1)$fatal(1,"IM1 lost");
ir=8'h5e;#1;if(imode!==2)$fatal(1,"IM2 lost");
$display("PASS NOP decode 576 contexts + HALT/IM controls = 580");$finish;end endmodule
'''
(w/'tb.sv').write_text(tb)
a=subprocess.run([os.environ['IVERILOG'],'-B',os.environ['IVL_ROOT'],'-g2012','-s','tb_nop_decode_r20_6','-o',str(w/'run.vvp'),str(w/'tb.sv'),str(r/'verification/cpu_1.v')],capture_output=True,text=True);assert a.returncode==0,a.stderr
a=subprocess.run([os.environ['VVP'],str(w/'run.vvp')],capture_output=True,text=True);out=a.stdout+a.stderr;(w/'result.log').write_text(out);assert a.returncode==0,out
(r/'verification_nop_decode_r20_6_result.json').write_text(json.dumps(dict(fresh_runs=580,decoded_contexts=576,control_cases=4,output=out,post_GHDL_decode_only=True,GOWIN_tested=False),indent=2)+'\n');print(out)
