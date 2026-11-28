"""Compare complete generated Verilog after equal-width wire alias elimination.
No gates, registers, port names, widths, clocks, or constants are abstracted.
"""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1]
def canonical(text):
 text=re.sub(r'/\*.*?\*/','',text,flags=re.S);text=re.sub(r'//[^\n]*','',text);parts=[];alias_count=0
 for m in re.finditer(r'\bmodule\b.*?\bendmodule\b',text,re.S):
  s=m[0];decl={};ports=set()
  for d in re.finditer(r'\b(input|output)\s*(\[\s*\d+\s*:\s*\d+\s*\])?\s*(\w+)\s*(?=[,)])',s.split(';',1)[0]):
   width=1
   if d[2]:
    a,b=map(int,re.findall(r'\d+',d[2]));width=abs(a-b)+1
   decl[d[3]]=(d[1],width);ports.add(d[3])
  pat=r'^\s*(input|output|wire|reg)\s*(\[\s*\d+\s*:\s*\d+\s*\])?\s*(\w+)\s*;'
  for d in re.finditer(pat,s,re.M):
   shape=re.sub(r'\s+','',d[2]or'');width=1
   if shape:
    a,b=map(int,re.findall(r'\d+',shape));width=abs(a-b)+1
   decl[d[3]]=(d[1],width)
   if d[1]in ['input','output']:ports.add(d[3])
  aliases={}
  for a in re.finditer(r'\bassign\s+(\w+)\s*=\s*(\w+)\s*;',s):
   lhs,rhs=a.group(1,2)
   if lhs not in ports and decl.get(lhs,('',0))[0]=='wire'and rhs in decl and decl[lhs][1]==decl[rhs][1]:aliases[lhs]=rhs
  def root(n):
   seen=set()
   while n in aliases:
    assert n not in seen;seen.add(n);n=aliases[n]
   return n
  s=re.sub(r'\bassign\s+(\w+)\s*=\s*(\w+)\s*;',lambda a:''if a[1]in aliases else a[0],s)
  s=re.sub(pat,lambda a:''if a[3]in aliases else a[0],s,flags=re.M)
  s=re.sub(r'\b\w+\b',lambda a:root(a[0]),s);alias_count+=len(aliases)
  generated={}
  def rename(a):
   if a[0]not in generated:generated[a[0]]='internal'+str(len(generated))
   return generated[a[0]]
  s=re.sub(r'\b(?:alu_)?n\d+(?:_[a-zA-Z0-9]+)*\b',rename,s)
  parts.append(re.sub(r'\s+','',s))
 return '\n'.join(parts),alias_count
if __name__=='__main__':
 rows=[]
 for name in ['cpu_1.v','cpu_diag.v','cpu_0.v','cpu_reference.v']:
  a,na=canonical((R/'doc/R32_compatibility_models'/name).read_text());b,nb=canonical((R/'verification'/name).read_text());same=a==b
  print(name,'equal-width alias graph identical',same,'aliases',na,nb)
  if not same:
   i=next((i for i,(x,y)in enumerate(zip(a,b))if x!=y),0);print('first difference',a[max(0,i-80):i+100],b[max(0,i-80):i+100])
  rows.append(dict(model=name,identical=same,normalization='comments; equal-width internal wire aliases; generated internal net names',before_aliases=na,after_aliases=nb,before_sha256=hashlib.sha256(a.encode()).hexdigest(),after_sha256=hashlib.sha256(b.encode()).hexdigest()))
 (R/'doc/R32_VHDL93_MODEL_EQUIVALENCE.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert all(r['identical']for r in rows)
