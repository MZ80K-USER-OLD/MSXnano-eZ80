from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent.parent;w=r/'verification_im0_com_r19'
cases=[(4,0,0,0,1,1,0,0),(15,7,1,0,1,1,0,0),(4,0,0,1,1,1,0,0),(4,0,0,0,0,1,0,0),(4,0,0,0,1,0,0,0),(4,0,0,0,1,1,1,0),(4,0,0,0,1,1,0,1)]
rows=[]
for q in cases:
 d,p,s,f,e,req,legacy,nd=q;path=w/('_'.join(map(str,q))+'.log');out=path.read_text()
 model=r/'verification'/('cpu_0.v' if not e else 'cpu_1.v' if nd else 'cpu_diag.v')
 assert path.stat().st_mtime>=model.stat().st_mtime,q
 expected='READY' if not req else 'UNSUPPORTED' if not e else 'NOT READY' if legacy or nd else 'FAIL stage 0' if f else 'PASS'
 assert 'EZ80IM0 R19: '+expected in out and 'PASS rst_com_r18' in out,out
 assert 'FATAL:' not in out,out
 if f:assert 'ADDR=0A8100 EXP=FE ACT=FF' in out,out
 rows.append({'case':q,'expected':expected,'output':out,'simulation_model_sha256':hashlib.sha256(model.read_bytes()).hexdigest()})
(r/'verification_im0_com_r19_result.json').write_text(json.dumps({'fresh_runs':7,'cases':rows,'COM_sha256':hashlib.sha256((r/'hardware_test/EZ80IM0.COM').read_bytes()).hexdigest(),'actual_COM_bytes':True,'private_IM0_cases':24,'BDOS_stub_EI_and_real_IM1_IRQ':True,'GOWIN_run':False,'hardware_run':False},indent=2)+'\n')
print('PASS IM0 actual COM: 7 release profiles collected')
