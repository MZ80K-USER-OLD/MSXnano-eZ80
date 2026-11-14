"""Independent RST frame/address oracle; flat CPU memory, not board mapping."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent/'rst_r18';r.mkdir(exist_ok=True)
plans=[dict(kind='suffix',src=s,dst=d,madl=m,mb=14,vec=v) for s in (0,1) for d in (0,1) for m in (0,1) for v in range(0,64,8)]
plans += [dict(kind='bare',src=s,dst=s,madl=1,mb=14,vec=v) for s in (0,1) for v in range(0,64,8)]
plans += [dict(kind='suffix',src=s,dst=d,madl=1,mb=0,vec=v) for s in (0,1) for d in (0,1) for v in (0,56)]
plans += [dict(kind='boundary',src=s,dst=d,madl=1,mb=14,vec=v) for s in (0,1) for d in (0,1) for v in (8,56)]
plans += [dict(kind='guard',src=s,dst=0,madl=m,mb=14,vec=56,pref=p) for s in (0,1) for m in (0,1) for p in ((0x52,0x5b) if s==0 else (0x40,0x49))]
plans += [dict(kind=kind,src=s,dst=d,madl=1,mb=14,vec=16) for kind in ('pending_nmi','pending_irq') for s in (0,1) for d in (0,1)]
assert len(plans)==112
for case,q in enumerate(plans):
 m={};vector={};checks=[];writes=[];pc=0;mode=0;mb=q['mb'];src=q['src'];dst=q['dst'];mad=q['madl'];vec=q['vec'];guard=q['kind']=='guard';pending=q['kind'].startswith('pending');ief=int(pending)
 sp0=1 if q['kind']=='boundary' else 0xc001;spl0=0x050001;sp=sp0;spl=spl0;acc=0xa6;flags=0xd7
 def at(a,md=1):
  global pc,mode;pc=a;mode=md
 def e(*xs):
  global pc
  for x in xs:m[pc]=x;pc=(pc+1)&0xffffff if mode else (mb<<16)|((pc+1)&0xffff)
 def snapshot(marker):checks.append(dict(pc=pc,adl=mode,madl=mad,acc=acc,flags=flags,sp=sp,spl=spl,ief=ief,marker=marker))
 def push(a,v):writes.append((a,v))
 m.update({0:0xc3,1:0,2:1})
 at(0x100,1);e(0xf3,0x31,sp0&255,sp0>>8,1,0xe7,0xe7,0x3e,0xa5,0xed,0x79,0x3e,0x5a,0xed,0x79,0x5b,0xc3,0,0x10,0x0a)
 at(0x0a1000);e(0x31,*spl0.to_bytes(3,'little'),0x3e,mb,0xed,0x6d)
 if mad:e(0xed,0x7d)
 e(1,flags,acc,0,0xc5,0xf1)
 if pending:e(0xed,0x56,0xfb,0)
 start=(0x0affff if q['kind']=='boundary' else 0x0a8000) if src else ((mb<<16)|(0xffff if q['kind']=='boundary' else 0x8200))
 e(0x5b if src else 0x40,0xc3,*start.to_bytes(3,'little')[:3 if src else 2]);at(start,src)
 if q['kind']!='bare':e(q.get('pref',((0x40,0x49),(0x52,0x5b))[src][dst]))
 e(0xc7+vec);retpc=pc
 if not guard:
  if dst==0:
   for v in ((retpc>>8)&255,retpc&255):sp=(sp-1)&65535;push((mb<<16)|sp,v)
   if src:spl=(spl-1)&0xffffff;push(spl,retpc>>16)
  else:
   for v in retpc.to_bytes(3,'little')[:3 if src else 2][::-1]:spl=(spl-1)&0xffffff;push(spl,v)
  spl=(spl-1)&0xffffff;push(spl,2+src)
  pushed_sp,pushed_spl=sp,spl;sp,spl=sp0,spl0
  if q['kind']=='pending_irq':ief=0
  snapshot(0xa6)
  e(0x5b,0xc3,0,0x70,0x0a)
  target=vec if dst else (mb<<16)|vec
  handler=0x0c9000 if dst else (mb<<16)|0x9000
  at(target,dst);sp,spl=pushed_sp,pushed_spl;ief=int(pending);snapshot(0)
  for j,v in enumerate([0xc3,*handler.to_bytes(3,'little')[:3 if dst else 2]]):vector[target+j]=v
  at(handler,dst)
  e(0x5b,0x32,0,4,3,0x5b if dst else 0x49,0xc9)
  if pending:
   if q['kind']=='pending_nmi':sp,spl=pushed_sp,pushed_spl;ip=target;im=dst
   else:sp,spl=sp0,spl0;ip=retpc;im=src
   for v in ip.to_bytes(3,'little')[:3 if im else 2][::-1]:spl=(spl-1)&0xffffff;push(spl,v)
   spl=(spl-1)&0xffffff;push(spl,2+im)
   at(0x66 if q['kind']=='pending_nmi' else 0x38);e(0xc3,0,0x10,0x0b)
   at(0x0b1000);e(0xf5,0x3e,0x5a,0x32,0x20,4,3,0xf1,0x5b,0xed,0x45 if q['kind']=='pending_nmi' else 0x4d)
 at(0x0a7000);e(0xf3,0xed,0x7e,0x3e,0,0xed,0x6d,0x40,0xc3,0,2)
 m[0x030400]=0;m[0x030420]=0
 lines=[f"initial_spl=24'h{spl0:06x};initial_sp=16'h{sp0:04x};",f'nchecks={len(checks)};nwrites={len(writes)};expected_entries={int(not guard)+int(pending)};guard={int(guard)};guard_kind={case};halt_pc=0;trigger_pc=0;pending_nmi={int(q['kind']=='pending_nmi')};pending_irq={int(q['kind']=='pending_irq')};']
 lines.append(f'nvector={len(vector)};')
 for i,(a,v) in enumerate(sorted(vector.items())):lines.append(f"va[{i}]=24'h{a:06x};vd[{i}]=8'h{v:02x};")
 for a,v in sorted(m.items()):lines.append(f"mem[24'h{a:06x}]=8'h{v:02x};")
 for i,x in enumerate(checks):
  lines.append(f"epc[{i}]=24'h{x['pc']:06x};eadl[{i}]={x['adl']};emad[{i}]={x['madl']};")
  for n,size in [('acc',8),('flags',8),('sp',16),('spl',24),('ief',1),('marker',8)]:lines.append(f"check_{n}[{i}]=1;e_{n}[{i}]={size}'h{x[n]:x};")
 for i,(a,v) in enumerate(writes):lines.append(f"ewa[{i}]=24'h{a:06x};ewd[{i}]=8'h{v:02x};")
 (r/f'case{case}.vh').write_text('\n'.join(lines)+'\n');(r/f'case{case}.json').write_text(json.dumps(dict(plan=q,checks=checks,writes=writes),indent=2)+'\n')
(r/'plans.json').write_text(json.dumps(plans,indent=2)+'\n')
(r/'select.vh').write_text('\n'.join(f'if(CASE=={i})begin\n `include "rst_r18/case{i}.vh"\nend' for i in range(len(plans)))+'\n')
print('built R18 RST cases',len(plans))
