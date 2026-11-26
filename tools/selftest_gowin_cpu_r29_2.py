from pathlib import Path
import json,argparse
from check_gowin_cpu_r29_2 import check
R=Path(__file__).resolve().parents[1];W=R/'verification_checker_r29_2';W.mkdir(exist_ok=True)
def fixture(n,invert=False,missing=False):
 s='''module T80_eZ80(input clk_54m,clear,stream_in,input[7:0]DI_Reg,input DI_FRAME_VALID);
wire VCC,GND,Stream_Long;wire[7:0]d;wire[6:1]Frame_State_1;wire Frame_State_7,Frame_State_0;wire meta;
VCC vc(.V(VCC));GND gc(.G(GND));
DFFE Stream_Long_s0(.Q(Stream_Long),.D(stream_in),.CLK(clk_54m),.CE(VCC));
'''
 s+=('INV mi(.O(meta),.I(DI_FRAME_VALID));\n'if invert else"LUT1 mi(.F(meta),.I0(DI_FRAME_VALID));defparam mi.INIT=2'h2;\n")
 s+="LUT1 d0(.F(d[0]),.I0(meta));defparam d0.INIT=2'h1;\n"
 for i,init in [(1,'02'),(2,'20'),(3,'88')]:s+=f"LUT3 d{i}(.F(d[{i}]),.I0(meta),.I1(Stream_Long),.I2(DI_Reg[0]));defparam d{i}.INIT=8'h{init};\n"
 for i in range(8):
  q='Frame_State_7'if i==7 else'Frame_State_0'if i==0 else f'Frame_State_1[{i}]';d=f'd[{i}]'if i<=3 else'GND';ty='DFFPE'if i==7 else'DFFCE';pin='PRESET'if i==7 else'CLEAR'
  s+=f'{ty} Frame_State_{i}_s1(.Q({q}),.D({d}),.CLK(clk_54m),.CE(VCC),.{pin}(clear));\n'
 s+='endmodule\nmodule G80A_eZ80(input clk_54m,clear,cap,valid_in,stream_in,input[7:0]DI_Reg);\nwire tag,nclk;\nINV ic(.O(nclk),.I(clk_54m));\n'
 if missing:s+='GND broken(.G(tag));\n'
 else:s+='DFFE DI_Frame_Valid_Reg_s0(.Q(tag),.D(valid_in),.CLK(nclk),.CE(cap));\n'
 s+='T80_eZ80 u0(.clk_54m(clk_54m),.clear(clear),.stream_in(stream_in),.DI_Reg(DI_Reg),.DI_FRAME_VALID(tag));\nendmodule\n'
 p=W/(n+'.vg');p.write_text(s);return p
rows=[]
for n,inv,missing,expected in [('good',False,False,None),('inverted_tag',True,False,'FSM logic differs'),('missing_ff',False,True,'FF missing')]:
 p=fixture(n,inv,missing)
 try:
  j=check(p);assert expected is None,(n,'bad fixture accepted');rows.append(dict(name=n,passed=True,checks=j['checks']))
 except RuntimeError as e:
  assert expected and expected in str(e),(n,str(e));rows.append(dict(name=n,expected_rejection=str(e),passed=True))
 print('PASS checker',n,flush=True)
a=argparse.ArgumentParser();a.add_argument('--r28');a.add_argument('--r29');args=a.parse_args()
if args.r28:
 j=check(args.r28,baseline=True);rows.append(dict(name='actual_R28',passed=True,checks=j['checks'],sha256=j['source_sha256']))
if args.r29:
 for baseline in [False,True]:
  try:check(args.r29,baseline=baseline)
  except RuntimeError as e:
   assert ('FSM logic differs'if baseline else'FF missing')in str(e);rows.append(dict(name='actual_R29_baseline'if baseline else'actual_R29',passed=True,expected_rejection=str(e)))
  else:raise AssertionError('Actual bad R29 accepted')
(W/'result.json').write_text(json.dumps(rows,indent=2)+'\n')
