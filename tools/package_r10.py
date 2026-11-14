"""Produce a self-contained release and check every archived byte."""
from pathlib import Path
import json,hashlib,zipfile
r=Path(__file__).resolve().parent.parent;out=r.parent/'r10-delivery';out.mkdir(exist_ok=True)
summary=json.loads((r/'verification_result.json').read_text());assert summary['series']=='restart R10'
assert summary['total_fresh_simulation_runs']==127,summary
files={}
for folder in ('fpga','hardware_test','sim','tools','doc'):
 for p in (r/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.cf','.vvp') and p.name!='SHA256SUMS.txt':files[str(p.relative_to(r))]=p.read_bytes()
files['README.md']=(r/'README.md').read_bytes()
for p in r.glob('verification*.json'):files[p.name]=p.read_bytes()
for folder in r.glob('verification*'):
 if folder.is_dir():
  for p in folder.rglob('*.log'):files['verification_logs/'+str(p.relative_to(r))]=p.read_bytes()
for p in (r/'hardware_test').glob('*.COM'):
 files[p.name]=p.read_bytes();(out/p.name).write_bytes(p.read_bytes())
files['TEST_COMMANDS.txt']=('R10 bitstream first. GOWIN project: fpga/project_eZ80/MSXNanoTang20K_eZ80.gprj\n'
 'EZ80ADL /RUN -> EZ80ADL P1: PASS (unchanged preloaded P1)\n'
 'EZ80CTL /RUN -> EZ80CTL R10: PASS (new control-flow test)\n'
 'EZ80F9 /RUN -> EZ80F9 R9: PASS (regression)\n'
 'Then SofaRun / Space Manbow play regression. Record LUT and post-route timing.\n'
 'Do not use EI/NMI while executing ADL. Mixed suffix CALL/RET/RST and ADL IRQ are not implemented.\n'
 'Memory mismatch diagnostics: stage, ADDR, EXP, ACT.\n').encode()
manifest=''.join(hashlib.sha256(v).hexdigest()+'  '+n+'\n' for n,v in sorted(files.items()))
files['doc/SHA256SUMS.txt']=manifest.encode();(r/'doc/SHA256SUMS.txt').write_text(manifest)
name='MSXnano_T80_eZ80_restart_R10';zpath=out/(name+'.zip')
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(files.items()):z.writestr(name+'/'+n,v)
 for p in sorted((r/'hardware_test').glob('*.COM')):z.writestr(p.name,p.read_bytes())
 z.writestr('TEST_COMMANDS.txt',files['TEST_COMMANDS.txt'])
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for n,v in files.items():assert z.read(name+'/'+n)==v,n
 for p in (r/'hardware_test').glob('*.COM'):
  for n in (p.name,name+'/'+p.name,name+'/hardware_test/'+p.name):assert z.read(n)==p.read_bytes(),n
record=dict(zip_name=zpath.name,zip_bytes=zpath.stat().st_size,zip_sha256=hashlib.sha256(zpath.read_bytes()).hexdigest(),archive_members=len(files)+10,project_members=len(files),COM_copies_per_test=3,verified_CRC_and_all_member_bytes=True,verification_summary=summary)
(out/'R10_RELEASE.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='verification_summary'},indent=2))
