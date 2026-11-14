from pathlib import Path
import json
r=Path(__file__).resolve().parent/'mixed_r14';r.mkdir(exist_ok=True)
plans=[dict(kind='basic',src=s,dst=d,mb=mb,madl=mad) for s in [0,1] for d in [0,1] for mb in [0,14] for mad in [0,1]]
plans += [dict(kind=kind,src=1,dst=0,mb=14,madl=0,cc=cc,take=t) for kind in ['conditional_call','conditional_ret'] for cc in range(8) for t in [0,1]]
plans += [dict(kind='nested',src=s,dst=d,mb=14,madl=1) for s in [0,1] for d in [0,1]]
plans += [dict(kind='boundary',src=s,dst=d,mb=14,madl=0) for s in [0,1] for d in [0,1]]
plans += [dict(kind='pending_nmi' if i<2 else 'pending_irq',src=i%2,dst=1-i%2,mb=14,madl=1) for i in range(4)]
plans += [dict(kind='guard',src=1,dst=0,mb=14,madl=0,guard=g) for g in ['bad_lis','bad_lil']]+[dict(kind='guard',src=0,dst=0,mb=14,madl=0,guard=g) for g in ['call_lis','call_lil']]
assert len(plans)==64
for case,plan in enumerate(plans):
 m={};checks=[];writes=[];labels={};pc=0;mode=0;sp=1 if plan['mb'] else 0xf000;spl=1 if plan['mb'] else 0x050001;sp0=sp;spl0=spl
 mb=plan['mb'];madl=plan['madl'];flags=0xd7;acc=0xa6;entries=0;trigger_pc=0;guard=0
 if 'cc' in plan:
  bit=[6,6,0,0,2,2,7,7][plan['cc']];required=plan['cc']%2
  flags=(0xd7 & ~(1<<bit)) | ((required if plan['take'] else 1-required)<<bit)
 def at(a,md=1):
  global pc,mode;pc=a;mode=md
 def e(*xs):
  global pc
  for x in xs:
   m[pc]=x;pc=((pc+1)&0xffffff) if mode else ((mb<<16)|((pc+1)&0xffff))
 def pointer_state(marker=None,ief=0):checks.append(dict(pc=pc,adl=mode,madl=madl,acc=acc,flags=flags,sp=sp,spl=spl,ief=ief,marker=marker))
 def push(addr,val):writes.append((addr&0xffffff,val))
 def make_frame(src,dst,ret):
  global sp,spl
  if not dst:
   for v in [(ret>>8)&255,ret&255]:sp=(sp-1)&0xffff;push((mb<<16)|sp,v)
   if src:spl=(spl-1)&0xffffff;push(spl,(ret>>16)&255)
  else:
   for v in ret.to_bytes(3,'little')[:3 if src else 2][::-1]:spl=(spl-1)&0xffffff;push(spl,v)
  spl=(spl-1)&0xffffff;push(spl,2+src)
 def restore(src,dst):
  global sp,spl
  if not dst:sp=(sp+2)&0xffff;spl=(spl+1+src)&0xffffff
  else:spl=(spl+3+src)&0xffffff
 def call(dst,target,op=0xcd):
  global entries
  e([0x40,0x52,0x49,0x5b][mode*2+dst],op,*target.to_bytes(3,'little')[:2+dst]);entries+=1
  return pc
 def ret(op=0xc9):e(0x5b if mode else 0x49,op)
 def cleanup():e(0xf3,0x5b,0xc3,0,0x70,0x0a)
 at(0,0);m[0]=0xc3;m[1]=0;m[2]=1
 # Boot is always bank zero; enter ADL before setting MBASE.
 at(0x100,1);e(0xf3,0x31,sp&255,sp>>8,1,0xe7,0xe7,0x3e,0xa5,0xed,0x79,0x3e,0x5a,0xed,0x79,0x5b,0xc3,0,0x10,0x0a)
 at(0x0a1000);e(0x31,*spl.to_bytes(3,'little'),0x3e,mb,0xed,0x6d)
 if madl:e(0xed,0x7d)
 e(0xed,0x56)
 e(1,flags,acc,0,0xc5,0xf1)
 if plan['kind'].startswith('pending'):e(0xfb,0)
 start=(0x0affff if plan['kind']=='boundary' else 0x0a8000) if plan['src'] else ((mb<<16)|(0xfffc if plan['kind']=='boundary' else 0x8200))
 e(0x5b if plan['src'] else 0x40,0xc3,*start.to_bytes(3,'little')[:3 if plan['src'] else 2]);at(start,plan['src'])
 target=0x0b9000 if plan['dst'] else (mb<<16)|0x9000
 if plan['kind']=='guard':
  guard=1;g=plan['guard']
  if g.startswith('bad'):
   # Poke the invalid mode at current SPL using a long data access.
   e(0x3e,4,0x5b,0x32,*spl.to_bytes(3,'little'),0x49 if g=='bad_lis' else 0x5b,0xc9)
  else:e(0x49 if g=='call_lis' else 0x5b,0xcd,0,0,0)
 else:
  cc=plan.get('cc',0);op=(0xc4+8*cc) if plan['kind']=='conditional_call' else 0xcd
  caller_mode=mode;after=call(plan['dst'],target,op);caller_pc=pc
  taken=plan['kind']!='conditional_call' or plan['take']
  if taken:make_frame(caller_mode,plan['dst'],after)
  pushed_sp,pushed_spl=sp,spl
  if taken:restore(caller_mode,plan['dst'])
  pointer_state(marker=0xa6 if taken else 0,ief=1 if plan['kind']=='pending_nmi' else 0)
  cleanup()
  if taken:
   at(target,plan['dst']);sp,spl=pushed_sp,pushed_spl
   if plan['kind']=='nested':
    nested_mode=1-plan['dst'];nested_target=0x0c9000 if nested_mode else (mb<<16)|0x9200
    nested_after=call(nested_mode,nested_target);midpc=pc
    make_frame(mode,nested_mode,nested_after);inner_sp,inner_spl=sp,spl;restore(mode,nested_mode)
    pointer_state(marker=0xa6);ret()
    at(nested_target,nested_mode);sp,spl=inner_sp,inner_spl
    pointer_state();e(0x5b,0x32,0,4,3);ret()
   else:
    if plan['kind']=='conditional_ret':
     ret(0xc0+8*cc)
     if not plan['take']:pointer_state(marker=0);ret()
    else:
     # This store changes neither A nor flags.
     e(0x5b,0x32,0,4,3);ret()
   if plan['kind']=='conditional_ret':
    # A taken RET must still mark the visited callee before the branch.
    # Move the marker store before RET without moving the caller addresses.
    at(target,plan['dst']);e(0x5b,0x32,0,4,3);ret(0xc0+8*cc)
    if not plan['take']:pointer_state(marker=0xa6);ret()
    checks=[x for x in checks if x['pc']!=target+2]
   if plan['kind'].startswith('pending'):
    # One mode frame interrupt is accepted at a whole-instruction boundary.
    saved_sp,saved_spl=sp,spl
    if plan['kind']=='pending_nmi':sp,spl=pushed_sp,pushed_spl;ip=target;im=plan['dst']
    else:sp,spl=sp0,spl0;ip=after;im=caller_mode
    for v in ip.to_bytes(3,'little')[:3 if im else 2][::-1]:spl=(spl-1)&0xffffff;push(spl,v)
    spl=(spl-1)&0xffffff;push(spl,2+im);entries+=1
    at(0x66 if plan['kind']=='pending_nmi' else 0x38);e(0xc3,0,0x10,0x0b)
    at(0x0b1000);e(0xf5,0x3e,0x5a,0x32,0x20,4,3,0xf1,0x5b,0xed,0x45 if plan['kind']=='pending_nmi' else 0x4d)
 # Independent clean exit, not a DOS/BIOS shim.
 at(0x0a7000);e(0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,0,2)
 m[0x030400]=0;m[0x030420]=0
 # Header and metadata consumed by the common WAIT/CEN/bus monitor.
 lines=['initial_spl=24\'h%06x;initial_sp=16\'h%04x;'%(spl0,sp0),f'nchecks={len(checks)};nwrites={len(writes)};expected_entries={entries};guard={guard};guard_kind={case};halt_pc=0;trigger_pc=0;',f'pending_nmi={int(plan["kind"]=="pending_nmi")};pending_irq={int(plan["kind"]=="pending_irq")};']
 for a,v in sorted(m.items()):lines.append("mem[24'h%06x]=8'h%02x;"%(a,v))
 for i,x in enumerate(checks):
  lines += [f"epc[{i}]=24'h{x['pc']:06x};eadl[{i}]={x['adl']};emad[{i}]={x['madl']};"]
  for name,size,field in [('acc',8,'acc'),('flags',8,'flags'),('sp',16,'sp'),('spl',24,'spl'),('ief',1,'ief'),('marker',8,'marker')]:
   v=x.get(field);lines.append(f'check_{name}[{i}]={int(v is not None)};')
   if v is not None:lines.append(f"e_{name}[{i}]={size}'h{v:x};")
 for i,(a,v) in enumerate(writes):lines.append(f"ewa[{i}]=24'h{a:06x};ewd[{i}]=8'h{v:02x};")
 (r/f'case{case}.vh').write_text('\n'.join(lines)+'\n');(r/f'case{case}.json').write_text(json.dumps(dict(plan=plan,checks=checks,writes=writes,entries=entries),indent=2)+'\n')
(r/'select.vh').write_text('\n'.join(f'if(CASE=={i})begin\n `include "mixed_r14/case{i}.vh"\nend' for i in range(len(plans)))+'\n')
(r/'plans.json').write_text(json.dumps(plans,indent=2)+'\n');print('built mixed R14 cases',len(plans))
