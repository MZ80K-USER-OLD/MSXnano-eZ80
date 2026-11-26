"""Conservative CPU metadata-FF/FSM check on a Gowin .vg, without vendor tools.
This is a cutpoint truth-table check, not full CPU or post-route timing simulation.
Unrecognized mappings are rejected for manual review; they never become PASS.
"""
from pathlib import Path
import re,json,argparse,hashlib,functools,sys

def modules(path):
 text=Path(path).read_text();out={}
 for name,body in re.findall(r'\bmodule\s+(\w+)\s*\((.*?)endmodule',text,re.S):
  cells={};drivers={}
  init={n:int(h,16)for n,h in re.findall(r"defparam\s+(\S+)\.INIT\s*=\s*\d+'h([0-9a-fA-F]+)",body)}
  for typ,n,part in re.findall(r'^\s*(\w+)\s+([^\s(]+)\s*\((.*?)\);',body,re.M|re.S):
   pins=dict(re.findall(r'\.(\w+)\((.*?)\)',part));cells[n]=(typ,pins)
   for pin in ['F','Q','O','SUM','COUT']:
    if pin in pins:drivers[pins[pin]]=(n,typ,pins,pin)
  out[name]=dict(body=body,cells=cells,drivers=drivers,init=init)
 return out

def check(path,baseline=False):
 mods=modules(path)
 if 'T80_eZ80'not in mods:raise RuntimeError('INCONCLUSIVE: T80_eZ80 module missing/renamed')
 core=mods['T80_eZ80'];cells=core['cells'];dr=core['drivers'];ini=core['init'];state={}
 for bit in range(8):
  found=[(n,ty,ps)for n,(ty,ps)in cells.items()if ty.startswith('DFF')and re.fullmatch('Frame_State_'+str(bit)+r'_s\d+',n)]
  if len(found)!=1:raise RuntimeError('INCONCLUSIVE: FSM encoding/instance name changed at bit '+str(bit))
  state[bit]=found[0]
 if 'P'not in state[7][1]:raise RuntimeError('INCONCLUSIVE: expected idle one-hot reset bit7 not found')
 roots=[state[i][2]['D']for i in range(8)]+[state[0][2]['CE']]
 def leaves(net,seen=None):
  if seen is None:seen=set()
  if net in seen:return set()
  seen.add(net)
  if net in ['VCC','GND']or "'"in net:return set()
  if net not in dr or dr[net][1].startswith('DFF'):return{net}
  _,ty,ps,_=dr[net]
  if not re.fullmatch(r'LUT[1-8]|INV|MUX2(?:_LUT[5-8])?',ty):raise RuntimeError('INCONCLUSIVE: unsupported FSM-cone primitive '+ty)
  return set().union(*(leaves(v,seen)for k,v in ps.items()if k not in ['F','O','Q','SUM','COUT']))
 boundary=set().union(*(leaves(x)for x in roots));meta=None;meta_info=None
 if not baseline:
  found=[]
  for mod,obj in mods.items():
   for n,(ty,ps)in obj['cells'].items():
    if ty.startswith('DFF')and re.search('DI_Frame_Valid_Reg',n,re.I):found.append((mod,n,ty,ps))
  if len(found)!=1:raise RuntimeError('REJECTED: independent DI_Frame_Valid_Reg FF missing/ambiguous')
  mod,n,ty,ps=found[0];q=ps['Q']
  if mod=='T80_eZ80':meta=q
  else:
   bindings=[]
   for _,(child,ports)in mods[mod]['cells'].items():
    if child=='T80_eZ80':bindings +=[pin for pin,value in ports.items()if value==q]
   if len(bindings)!=1:raise RuntimeError('INCONCLUSIVE: metadata FF to CPU-port connection needs manual trace')
   meta=bindings[0]
  if meta not in boundary:raise RuntimeError('REJECTED: metadata FF does not reach frame-mode transition cone')
  clock=ps.get('CLK');clock_info=None
  if 'N'in ty[3:]:clock_info=dict(edge='falling',clock=clock)
  else:
   inv=[(cn,cp)for cn,(ct,cp)in mods[mod]['cells'].items()if ct=='INV'and cp.get('O')==clock]
   if len(inv)!=1:raise RuntimeError('INCONCLUSIVE: capture clock polarity needs manual trace')
   clock_info=dict(edge='falling via INV',clock=inv[0][1]['I'])
  meta_info=dict(module=mod,cell=n,type=ty,core_boundary=meta,clock=clock_info,enable=ps.get('CE'))
 def evaluate(byte,stream,tag):
  ov={net:0 for net in boundary}
  for n,(ty,ps)in cells.items():
   if not ty.startswith('DFF'):continue
   v=None
   if n==state[4][0]:v=1
   elif re.fullmatch(r'Frame_TS_[01]_s\d+',n):v=1
   elif re.fullmatch(r'Stream_Long_s\d+',n):v=stream
   elif re.fullmatch(r'Extensions_Enabled_s\d+',n):v=1
   if v is not None:ov[ps['Q']]=v
  ov.update({'Stream_Long':stream,'Extension_State_i':1,'bus_clk_3m6_54':1,'bus_clk_3m6_prev_54':0,'wait_io_ff':1,'counter_reset[20]':1,'counter_reset[19]':0,'counter_reset[18]':0,'n1042_3':1,'n115_7':0,'IRQ_IM0':0})
  for i in range(8):ov[f'DI_Reg[{i}]']=(byte>>i)&1
  if meta is not None:ov[meta]=tag
  @functools.lru_cache(None)
  def val(net):
   if net in ov:return ov[net]
   if net in ['GND',"1'b0"]:return 0
   if net in ['VCC',"1'b1"]:return 1
   if net not in dr:raise RuntimeError('INCONCLUSIVE: unresolved boundary net '+net)
   name,ty,ps,_=dr[net]
   if ty.startswith('DFF'):return 0
   if ty.startswith('LUT'):
    if name not in ini:raise RuntimeError('INCONCLUSIVE: missing LUT INIT '+name)
    return(ini[name]>>sum(val(ps['I'+str(i)])<<i for i in range(int(ty[3:]))))&1
   if ty=='INV':return 1-val(ps['I'])
   if ty.startswith('MUX2'):return val(ps['I1'if val(ps['S0'])else'I0'])
   raise RuntimeError('INCONCLUSIVE: unsupported evaluation '+ty)
  if val(roots[8])!=1:raise RuntimeError('INCONCLUSIVE: frame completion CE is not active at this cutpoint')
  return sum(val(roots[i])<<i for i in range(8))
 count=0
 for stream in [0,1]:
  for byte in range(256):
   valid=int(byte in [2,3])
   for flip in ([0]if baseline else[0,1]):
    tag=valid^flip;want=(8 if stream else 4 if byte&1 else 2)if tag else 1;got=evaluate(byte,stream,tag)
    if got!=want:raise RuntimeError(f'REJECTED: FSM logic differs byte={byte:02X} stream={stream} meta={tag} got={got:02X} expected={want:02X}')
    count+=1
 return dict(passed=True,source_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),checks=count,normal_checks=512,contradictory_metadata_checks=0 if baseline else 512,baseline=baseline,metadata_capture=meta_info,cutpoint='one-hot frame_mode=bit4; ordinary return; completion CE=1; other boundary values zero except listed source defaults',zero_delay_only=True,full_CPU_simulated=False,timing_verified=False)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('netlist');a.add_argument('--baseline',action='store_true');a.add_argument('--output');p=a.parse_args()
 try:
  result=check(p.netlist,p.baseline);text=json.dumps(result,indent=2)
  if p.output:Path(p.output).write_text(text+'\n')
  print(text)
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
