from pathlib import Path
import subprocess,os,re,hashlib,json,shutil
r=Path(__file__).resolve().parent.parent; q=r/'verification';q.mkdir(exist_ok=True)
local_g=r.parents[1]/'local-ghdl/usr/bin/ghdl'
g=os.environ.get('GHDL',str(local_g) if local_g.is_file() else shutil.which('ghdl') or 'ghdl')
env=os.environ.copy();local_prefix=r.parents[1]/'local-ghdl/usr/lib/ghdl/mcode/vhdl'
if local_prefix.is_dir():env.setdefault('GHDL_PREFIX',str(local_prefix))
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 p=subprocess.run([g,'-a','--std=08','-fsynopsys',str(r/'fpga/G80A_eZ80'/(n+'_ez80.vhd'))],cwd=q,env=env,capture_output=True,text=True);assert not p.returncode,p.stderr
for name,ext,diag in [('cpu_1',True,False),('cpu_diag',True,True),('cpu_0',False,False)]:
 p=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches',f'-gDATA_EXTENDED={str(ext).lower()}',f'-gDIAGNOSTICS={str(diag).lower()}','G80A_eZ80'],cwd=q,env=env,capture_output=True,text=True);assert not p.returncode,p.stderr
 s=re.sub(r'\bdo\b','data_out',p.stdout);needle='  wire [7:0] alu_q;'
 if s.count(needle)==2:
  at=s.index(needle,s.index(needle)+1);s=s[:at]+s[at:].replace(needle,'  wire [7:0] alu_port_q;',1);names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1;s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
 (q/(name+'.v')).write_text(s);print('synthesized',name,flush=True)
(q/'r36_rtl_sha256.json').write_text(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(r/'fpga/G80A_eZ80').glob('*.vhd')},indent=2))

# Exact R33 complete CPU/wrapper source, for cycle-by-cycle comparison.
ref=q/'reference_r33';ref.mkdir(exist_ok=True)
for n in ['t80_pack','t80_reg','t80_alu','t80_mcode','t80','g80a']:
 src=r/'sim/reference_r33'/(n+'_ez80.vhd')
 p=subprocess.run([g,'-a','--std=08','-fsynopsys',str(src)],cwd=ref,env=env,capture_output=True,text=True);assert not p.returncode,p.stderr
p=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches','-gDATA_EXTENDED=true','-gDIAGNOSTICS=true','G80A_eZ80'],cwd=ref,env=env,capture_output=True,text=True);assert not p.returncode,p.stderr
s=re.sub(r'\bdo\b','data_out',p.stdout);needle='  wire [7:0] alu_q;'
if s.count(needle)==2:
 at=s.index(needle,s.index(needle)+1);s=s[:at]+s[at:].replace(needle,'  wire [7:0] alu_port_q;',1);names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1;s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
mods=re.findall(r'^module\s+(\w+)',s,re.M)
s=re.sub(r'\b('+ '|'.join(map(re.escape,mods))+r')\b',lambda m:m[0]+'_reference',s)
(q/'cpu_reference.v').write_text(s)
print('synthesized exact R33 reference',flush=True)
# Normal profile reference for the focused input capture test.
p=subprocess.run([g,'--synth','--std=08','-fsynopsys','--out=verilog','--latches','-gDATA_EXTENDED=true','-gDIAGNOSTICS=false','G80A_eZ80'],cwd=ref,env=env,capture_output=True,text=True);assert not p.returncode,p.stderr
s=re.sub(r'\bdo\b','data_out',p.stdout);needle='  wire [7:0] alu_q;'
if s.count(needle)==2:
 at=s.index(needle,s.index(needle)+1);s=s[:at]+s[at:].replace(needle,'  wire [7:0] alu_port_q;',1);names=re.findall(r'assign (alu_n\d+) = alu_q;',s);assert len(names)==1;s=s.replace(f'assign {names[0]} = alu_q;',f'assign {names[0]} = alu_port_q;').replace('.q(alu_q)','.q(alu_port_q)')
mods=re.findall(r'^module\s+(\w+)',s,re.M)
s=re.sub(r'\b('+ '|'.join(map(re.escape,mods))+r')\b',lambda m:m[0]+'_reference',s)
(q/'cpu_reference_normal.v').write_text(s)
print('synthesized exact R33 normal reference',flush=True)
