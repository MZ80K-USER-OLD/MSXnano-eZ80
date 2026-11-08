from pathlib import Path
import json
r=Path(__file__).resolve().parent/'madl_r13';r.mkdir(exist_ok=True)
plans=[]
for adl in [0,1]:
 for kind in ['IM1','IM2','NMI']:
  for mb in [0,14]:plans.append(dict(type='entry',adl=adl,kind=kind,mb=mb))
for current in [0,1]:
 for prefix in [0x49,0x5b]:
  for target in [0,1]:plans.append(dict(type='return',adl=current,prefix=prefix,target=target,mb=14))
plans += [dict(type='flags',adl=1,mb=0),dict(type='pending_nmi',adl=0,mb=14),dict(type='pending_irq',adl=1,mb=14)]
for guard in ['mode','rst','short']:plans.append(dict(type='guard',guard=guard,adl=1,mb=14))
for case,plan in enumerate(plans):
 m={};checks=[];frames=[];labels={};p=0;source=0;mb=plan['mb'];adl=plan['adl'];sp0=0xf000;spl0=0x050001;fault_guard=0;trigger_pc=0;restore_ief=0;expected_entries=0
 def at(a):
  global p;p=a
 def e(*vals):
  global p
  for v in vals:m[p]=v;p+=1
 def ld(op,value):e(op,*value.to_bytes(3,'little'))
 def state(mode=None,a=None,f=None,madl=1,sp=None,spl=None,ief=None,marker=None):checks.append(dict(pc=p,adl=adl if mode is None else mode,acc=a,flags=f,madl=madl,sp=sp,spl=spl,ief=ief,marker=marker))
 def flags(a,f,wide=True):e(1,f,a,*([0] if wide else []),0xc5,0xf1)
 def poke(address,value):e(0x3e,value,0x32,*address.to_bytes(3,'little'))
 def finish():e(0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,0,2)
 def irq_handlers():
  for addr,target in [(0x38,0x0b0000),(0x66,0x0b1000)]:at(addr);e(0xc3,*target.to_bytes(3,'little'))
  for i,v in enumerate([0,0x20,0x0b]):m[0x0c20fe+i]=v
  for addr,isnmi in [(0x0b0000,False),(0x0b1000,True),(0x0b2000,False)]:
   at(addr);e(0xf5)
   # Save IEF2 in flags from LD A,I; restore the interrupted AF before return.
   e(0xed,0x57,0xf5,0xc1,0xed,0x43,0x10,4,3)
   e(0x3e,0xa1 if isnmi else 0x5a,0x32,0,4,3,0xf1,0x5b,0xed,0x45 if isnmi else 0x4d)
 at(0);e(0xc3,0,1)
 at(0x100);e(0xf3,0x31,0,0xf0,1,0xe7,0xe7,0x3e,0xa5,0xed,0x79,0x3e,0x5a,0xed,0x79,0x5b,0xc3,0,0,0x0a)
 at(0x0a0000);ld(0x31,0x050080);e(0x3e,mb,0xed,0x6d);ld(0x21,0x000c20);e(0xed,0xc7)
 if plan['type'] in ['entry','pending_nmi','pending_irq']:
  kind=plan.get('kind','IM1' if plan['type']=='pending_nmi' else 'NMI');plan['kind']=kind
  if mb: spl0=1
  # Pending scenarios retain a private SPL to make nested-frame expectations readable.
  if plan['type'].startswith('pending'):spl0=0x050001
  ld(0x31,spl0);e(0xed,0x7d)
  if not adl:e(0x40,0xc3,0,0x82);at((mb<<16)|0x8200)
  flags(0xa6,0xd7,adl==1);e(0xed,0x5e if kind=='IM2' else 0x56)
  restore_ief=int(kind=='NMI' and mb!=0)
  if kind=='NMI':
   if restore_ief:e(0xfb,0)
   e(0x76);labels['halt']=p-1;labels['after']=p
  else:
   trigger_pc=p;e(0xfb,0x3e,0xa6);labels['after']=p
  state(a=0xa6,f=0xd7,sp=sp0,spl=spl0,ief=0 if plan['type']=='pending_irq' else restore_ief,marker=0x5a if kind!='NMI' or plan['type']=='pending_irq' else 0xa1)
  e(0xf3,0x5b,0xc3,0,0x40,0x0a)
  at(0x0a4000);finish();irq_handlers();m[0x030400]=0;m[0x030410]=0
  ret=labels['after'];data=ret.to_bytes(3,'little')[:3 if adl else 2][::-1]+bytes([3 if adl else 2])
  frames.append(dict(sp=spl0,bytes=list(data)))
  expected_entries=1
  if plan['type']=='pending_nmi':
   frames.append(dict(sp=(spl0-len(data))&0xffffff,bytes=list((0x38).to_bytes(3,'little')[::-1])+[3]));expected_entries=2
  if plan['type']=='pending_irq':
   frames.append(dict(sp=spl0,bytes=list(ret.to_bytes(3,'little')[::-1])+[3]));expected_entries=2
 elif plan['type']=='return':
  spl0=0xffffff;sp0=0xffff;target=plan['target'];prefix=plan['prefix'];restore_ief=target
  ld(0x31,spl0);e(0x40,0x31,0xff,0xff)
  dest=0x0d0200 if target else 0x0e0200
  bytes_spl=[2|target]
  if prefix==0x5b:bytes_spl += list(dest.to_bytes(3,'little')[:3 if target else 2])
  elif target:bytes_spl += [dest>>16]
  for i,v in enumerate(bytes_spl):poke((spl0+i)&0xffffff,v)
  if prefix==0x49:
   for i,v in enumerate(dest.to_bytes(3,'little')[:2]):poke((mb<<16)|((sp0+i)&0xffff),v)
  e(0xed,0x7d)
  if not adl:e(0x40,0xc3,0,0x82);at(0x0e8200)
  flags(0x5a,0xa5,adl==1)
  # Reset the initial stack after AF seeding; the synthetic frame must be untouched.
  if adl:ld(0x31,spl0)
  else:e(0x31,0xff,0xff)
  if restore_ief:e(0xfb,0)
  e(prefix,0xed,0x45 if target else 0x4d)
  at(dest);state(mode=target,a=0x5a,f=0xa5,sp=(sp0+2)&0xffff if prefix==0x49 else sp0,spl=(spl0+len(bytes_spl))&0xffffff,ief=restore_ief)
  e(0xf3,0x5b,0xc3,0,0x40,0x0a);at(0x0a4000);finish()
 elif plan['type']=='flags':
  e(0xed,0x5e)
  for mode in [1,0]:
   if not mode:e(0x40,0xc3,0,0x80);at(0x8000)
   for v in range(256):
    f=(v*37)^0xd7;f&=255;flags(v,f,mode==1);e(0xed,0x7d);state(mode=mode,a=v,f=f,madl=1)
    e(0xed,0x7e);state(mode=mode,a=v,f=f,madl=0)
  e(0x5b,0xc3,0,0x40,0x0a);at(0x0a4000);finish()
 else:
  spl0=0x050001;ld(0x31,spl0);e(0xed,0x7d)
  if plan['guard']=='mode':poke(spl0,4);e(0x5b,0xed,0x4d)
  elif plan['guard']=='rst':e(0xcf)
  else:e(0x40,0xed,0x4d)
  labels['guard_pc']=p;fault_guard=1
 lines=[f"mem[24'h{a:06x}]=8'h{v:02x};" for a,v in sorted(m.items())]
 for i,c in enumerate(checks):
  lines += [f"epc[{i}]=24'h{c['pc']:06x};",f"eadl[{i}]={c['adl']};",f"emad[{i}]={c['madl']};"]
  for name,size in [('acc',8),('flags',8),('sp',16),('spl',24),('ief',1),('marker',8)]:
   value=c[name];lines += [f"check_{name}[{i}]={int(value is not None)};",f"e_{name}[{i}]={size}'h{(value or 0):x};"]
 lines += [f'nchecks={len(checks)};',f'guard={fault_guard};',f"initial_sp=16'h{sp0:04x};",f"initial_spl=24'h{spl0:06x};",f"trigger_pc=24'h{trigger_pc:06x};",f"halt_pc=24'h{labels.get('halt',0):06x};",f'expected_entries={expected_entries};',f'pending_nmi={int(plan["type"]=="pending_nmi")};',f'pending_irq={int(plan["type"]=="pending_irq")};',f'guard_kind={0 if plan.get("guard")=="mode" else 1 if plan.get("guard")=="rst" else 2};']
 wi=0
 for frame in frames:
  for i,v in enumerate(frame['bytes']):lines += [f"ewa[{wi}]=24'h{(frame['sp']-1-i)&0xffffff:06x};",f"ewd[{wi}]=8'h{v:02x};"];wi+=1
 lines.append(f'nwrites={wi};')
 (r/f'case{case}.vh').write_text('\n'.join(lines)+'\n');(r/f'case{case}.json').write_text(json.dumps(dict(plan=plan,checks=checks,frames=frames,labels=labels),indent=2)+'\n')
(r/'plans.json').write_text(json.dumps(plans,indent=2)+'\n');print('built MADL cases',len(plans))

(r/'select.vh').write_text('case(CASE)\n'+''.join(f'{i}:begin\n `include "madl_r13/case{i}.vh"\nend\n' for i in range(len(plans)))+'endcase\n')
