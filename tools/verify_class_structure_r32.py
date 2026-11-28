"""Check unchanged execution bodies/capture guards and all binary byte classes.
This is source-structure equivalence plus GHDL evaluation, not post-route proof.
"""
from pathlib import Path
import re,json,hashlib,os,subprocess
R=Path(__file__).resolve().parents[1];W=R/'verification_class_structure_r32';W.mkdir(exist_ok=True)
def clean(s):return re.sub(r'--[^\n]*',lambda m:' '*len(m[0]),s)
def norm(s):return re.sub(r'\s+','',clean(s)).lower()
def cases(s):
 c=clean(s);stack=[];out=[]
 pat=r'\bend\s+case\b|\bcase\s+([^\n;]+?)\s+is\b|\bwhen\s+((?:(?:[xX]"[0-9a-fA-F]+"|"[01]+"|\d+|others)\s*\|?\s*)+)=>'
 for m in re.finditer(pat,c,re.I):
  if re.match(r'end\s+case',m[0],re.I):
   q=stack.pop();q['end']=m.start();q['tail']=m.end()
   if q['expr']=='irb'or re.fullmatch(r'to_integer\(unsigned\((base|cb|ed)_group\)\)',q['expr']):out.append(q)
  elif m[1]is not None:stack.append(dict(expr=re.sub(r'\s+','',m[1]).lower(),start=m.start(),choices=[]))
  elif stack:
   q=stack[-1]
   if q['expr']=='irb'or re.fullmatch(r'to_integer\(unsigned\((base|cb|ed)_group\)\)',q['expr']):q['choices'].append(dict(start=m.start(),end=m.end(),text=m[2].strip()))
 return sorted(out,key=lambda q:q['start'])
a=(R/'sim/reference_r31/t80_mcode_ez80.vhd').read_text();b=(R/'fpga/G80A_eZ80/t80_mcode_ez80.vhd').read_text();old=cases(a);new=cases(b);assert len(old)==len(new)==3
maps=[];proof=[]
for page,x,y in zip(['Base','CB','ED'],old,new):
 expected=[None]*256;other=None
 for i,ch in enumerate(x['choices']):
  if ch['text'].lower()=='others':other=i
  else:
   vals=[int(v,2)if v else int(h,16)for v,h in re.findall(r'"([01]{8})"|[xX]"([0-9a-fA-F]{2})"',ch['text'])]
   for v in vals:assert expected[v]is None;expected[v]=i
  ends=x['choices'][i+1]['start']if i+1<len(x['choices'])else x['end'];body=norm(a[ch['end']:ends])
  selected=next((j for j,c in enumerate(y['choices'])if c['text']==str(i)),None)
  if selected is None:assert ch['text'].lower()=='others';selected=next(j for j,c in enumerate(y['choices'])if c['text'].lower()=='others')
  nc=y['choices'][selected];ne=y['choices'][selected+1]['start']if selected+1<len(y['choices'])else y['end'];assert body==norm(b[nc['end']:ne]),(page,i)
  proof.append(dict(page=page,group=i,body_sha256=hashlib.sha256(body.encode()).hexdigest(),unchanged=True))
 if other is not None:expected=[other if v is None else v for v in expected]
 assert all(v is not None for v in expected);maps.append(expected)
 def replace(s,q):return s[:q['start']]+'MAIN_CLASS_'+page+s[q['tail']:]
# Surrounding execution code is unchanged, apart from group inputs/sensitivity.
for i in range(2,-1,-1):
 a=a[:old[i]['start']]+'MAIN_CLASS_'+str(i)+a[old[i]['tail']:]
 b=b[:new[i]['start']]+'MAIN_CLASS_'+str(i)+b[new[i]['tail']:]
b=re.sub(r'^\s*(?:Base|CB|ED)_Group\s*:\s*in\s+\w+_group_t;\n','',b,flags=re.M)
b=b.replace('process (Base_Group, CB_Group, ED_Group, Exec_Control','process (Exec_Control')
assert norm(a)==norm(b),'surrounding mcode changed'
# Capture guards are identical: remove only the added group assignments/declarations/map.
a=(R/'sim/reference_r31/t80_ez80.vhd').read_text();b=(R/'fpga/G80A_eZ80/t80_ez80.vhd').read_text()
captures=list(re.finditer(r'\bIR\s*<=\s*([^;]+);',b));assert len(captures)==4
for capture in captures:
 tail=b[capture.end():]
 for name in ['Base','CB','ED']:
  m=re.match(name+r'_Group<=Decode_'+name+r'_Group\(([^;]+)\);',tail)
  assert m and norm(m[1])==norm(capture[1]),'class/IR capture argument mismatch'
  tail=tail[m.end():]
for name in ['Base','CB','ED']:
 b=re.sub(r'^\s*signal '+name+r'_Group\s*:\s*\w+_group_t;\n','',b,flags=re.M)
 b=re.sub(name+r'_Group<=Decode_'+name+r'_Group\([^;]+\);','',b)
b=b.replace('            Base_Group=>Base_Group, CB_Group=>CB_Group, ED_Group=>ED_Group,\n','')
assert norm(a)==norm(b),'IR capture guards/other core behavior changed'
# Execute the actual new VHDL classifiers for every byte; expected classes come
# directly from the untouched R31 case choices above, not the new map JSON.
decls=[];checks=[]
for name,vals in zip(['Base','CB','ED'],maps):
 decls.append('constant '+name+'_expected:table_t:=('+','.join(str(v)for v in vals)+');')
 checks.append('assert to_integer(unsigned(Decode_'+name+'_Group(std_logic_vector(to_unsigned(op,8)))))='+name+'_expected(op) report "wrong '+name+' group" severity failure;')
tb='library ieee;use ieee.std_logic_1164.all;use ieee.numeric_std.all;use work.T80_eZ80_Pack.all;entity tb_classes is end;architecture sim of tb_classes is type table_t is array(0 to 255)of natural;'+''.join(decls)+'begin process begin for op in 0 to 255 loop '+''.join(checks)+'end loop;report "PASS binary classes 768";wait;end process;end;'
(W/'tb.vhd').write_text(tb);g=os.environ['GHDL']
for p in [R/'fpga/G80A_eZ80/t80_pack_ez80.vhd',W/'tb.vhd']:
 q=subprocess.run([g,'-a','--std=08','-fsynopsys',str(p)],cwd=W,capture_output=True,text=True);assert not q.returncode,q.stderr
q=subprocess.run([g,'-r','--std=08','-fsynopsys','tb_classes','--assert-level=error'],cwd=W,capture_output=True,text=True);assert not q.returncode and'PASS binary classes 768'in q.stdout+q.stderr
(W/'run.log').write_text(q.stdout+q.stderr)
result=dict(execution_bodies=len(proof),bodies_unchanged=proof,mcode_surrounding_logic_unchanged=True,core_capture_guards_unchanged=True,capture_arguments_match_IR=True,GHDL_classifications=768,binary_opcode_invariant=True,valid_reset_and_capture_assumed=True,post_route=False,passed=True)
(W/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS structure: 95 bodies, surrounding logic, capture guards; GHDL classes 768')
