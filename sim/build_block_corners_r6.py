from pathlib import Path
import json
root=Path(__file__).resolve().parent.parent
src=(root/'hardware_test/build_data_r3.py').read_text()
exec(src[:src.index("label('START')")],globals());r=root/'sim/block_corners';r.mkdir(exist_ok=True)
rows=[]
label('START');emit(0xdd,0xe5,0xfd,0xe5,0xf3);ref([0xed,0x73],'SAVED_SPS');emit(0xed,0x56);gate(0xa5);gate(0x5a)
# name, opcode, count, steps, A, prefix, trigger (read/write/prefix/last), IRQ enabled
cases=[('LDI',0xa0,0x10001,1,0x22,0x49,1,0),('LDD',0xa8,0x10000,1,0x22,0x5b,1,0),
 ('LDIR',0xb0,3,3,0x22,0x49,1,1),('LDDR',0xb8,3,3,0x22,0x5b,2,1),
 ('CPI',0xa1,0x10001,1,0x22,0x49,1,0),('CPD',0xa9,0x10000,1,0x10,0x5b,1,0),
 ('CPIR',0xb1,3,2,0x22,0x49,1,1),('CPDR',0xb9,3,3,0x44,0x5b,4,1),
 ('LDIR1',0xb0,1,1,0x22,0x49,4,1),('CPIRmatch',0xb1,3,1,0x11,0x5b,3,1),
 ('SIS',0xb0,3,3,0x22,0x40,1,0),('SIL',0xb0,3,3,0x22,0x52,3,1),
 ('LDIzero',0xa0,0,1,0x22,0x49,1,0),('lockedLDIR',0xb0,3,3,0x22,0,1,1),('lockedCPIR',0xb1,3,2,0x22,0,3,1)]
for n,(name,op,count,steps,acc,pref,trigger,irq) in enumerate(cases):
 stage(chr(65+n));emit(0xaf,0x32,0xb2,0,0x32,0xb0,0,0x3e,n,0x32,0xb1,0)
 dec=bool(op&8);compare=bool(op&1);short=pref in (0,0x40,0x52);direction=-1 if dec else 1
 source=0x9000 if short else (0x030000 if dec else 0x02ffff)
 dest=0x9100 if short else (0x090000 if dec else 0x08ffff)
 vals=[0x11,0x22,0x33] if compare else [0x31,0x32,0x33]
 for i in range(steps):
  loadpair('HL',source+direction*i);emit(0x3e,vals[i]);indir('HL',True)
  if not compare:
   loadpair('HL',dest+direction*i);emit(0xaf);indir('HL',True)
 loadpair('SP',0x050080);loadpair('HL',source|(0x0b0000 if short else 0));loadpair('DE',dest|(0x0c0000 if short else 0));loadpair('BC',count|(0xa10000 if short else 0))
 # Arm after setup; initialize AF without disturbing BC.
 emit(0x3e,1,0x32,0xb2,0,0xc5,1,0xc5 if not compare else 1,acc,0xc5,0xf1,0xc1)
 if pref==0:
  emit(0xf5,0xc5);gate(0);emit(0xc1,0xf1)
 emit(0xfb if irq else 0xf3,0)
 label(f'CASE_{n}_BLOCK');emit(*([pref] if pref else []),0xed,op);label(f'CASE_{n}_AFTER');emit(0xf3);sa('END_A')
 emit(0xf5,0xfd,0xe1);ref([0xfd,0x22],'FLAGS');emit(0xaf,0x32,0xb2,0)
 if pref==0:
  emit(0xc5);gate(0xa5);gate(0x5a);emit(0xc1)
 spcheck(0x050080)
 mask=0xffff if short else 0xffffff;remaining=(count-steps)&mask
 capture_three({'BC':remaining|(0xa10000 if short else 0),'HL':((source+direction*steps)&mask)|(0x0b0000 if short else 0),'DE':(dest if compare else ((dest+direction*steps)&mask))|(0x0c0000 if short else 0)})
 la('END_A');check(acc)
 if compare:
  result=(acc-vals[steps-1])&255
  flags=(0x80 if result&128 else 0)|(0x40 if result==0 else 0)|(0x10 if (acc&15)<(vals[steps-1]&15) else 0)|2|1|(4 if remaining else 0)
 else:flags=0xc1|(4 if remaining else 0)
 la('FLAGS');emit(0xe6,0xd7);check(flags)
 emit(0x3a,0xb0,0);check(irq)
 if not compare:
  for i in range(steps):readcheck(dest+direction*i,vals[i])
 interrupt_step=steps if trigger==4 else 1
 repeating=bool(op&0x10) and interrupt_step<steps
 rows.append(dict(case=n,name=name,prefix=pref,opcode=op,count=count,steps=steps,irq=irq,trigger=trigger,interrupt_step=interrupt_step,restart=repeating))
emit(0x3e,1);sa('STATUS');ref([0x11],'MSG_PASS');ref([0xc3],'FINISH')
footer=src[src.index("label('SUBROUTINE')"):].replace('EZ80D3','EZ80B6').replace('`define R3_','`define B6_').replace(' R3',' R6')
footer=footer.replace('for at,name,off,i in bytefix:',"label('FLAGS');emit(0,0)\nlabel('END_A');emit(0)\nfor at,name,off,i in bytefix:")
exec(footer,globals())
for row in rows:
 n=row['case'];row['block_pc']=labels[f'CASE_{n}_BLOCK'];row['after_pc']=labels[f'CASE_{n}_AFTER']
(r/'vectors.json').write_text(json.dumps(rows,indent=2)+'\n')
(r/'case_plan.vh').write_text('\n'.join(f"block_pc[{v['case']}]=16'h{v['block_pc']:04x};after_pc[{v['case']}]=16'h{v['after_pc']:04x};trigger_kind[{v['case']}]={v['trigger']};irq_expected[{v['case']}]={v['irq']};steps_expected[{v['case']}]={v['steps']};irq_step[{v['case']}]={v['interrupt_step']};restart_expected[{v['case']}]={int(v['restart'])};" for v in rows)+'\n')

(r/'EZ80B6.json').write_text(json.dumps({'bytes':len(b),'sha256':__import__('hashlib').sha256(b).hexdigest(),'labels':labels,'simulation_only':True,'fixture_SPS':0xeffa,'IM1_vector':'0038 -> 00C0; testbench only','cases':rows},indent=2)+'\n')
