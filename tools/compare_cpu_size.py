"""Compare three standalone CPU Gowin PnR text reports or ZIPs containing one report."""
import argparse
from pathlib import Path
import re
import zipfile

def read_report(path):
 path=Path(path)
 if zipfile.is_zipfile(path):
  with zipfile.ZipFile(path) as z:
   names=[n for n in z.namelist() if n.lower().endswith('.rpt.txt')]
   if len(names)!=1:raise ValueError(f'{path}: expected exactly one .rpt.txt, found {len(names)}')
   data=z.read(names[0])
 else:data=path.read_bytes()
 return data.decode('utf-8-sig',errors='replace')

def parse_report(text):
 result={}
 for name in ['Logic','Register','CLS','BSRAM','DSP']:
  m=re.search(r'^\s*'+name+r'\s*\|\s*([\d.]+)\s*/\s*([\d.]+)\s*\|\s*(\d+)%',text,re.M)
  if not m:raise ValueError(f'Resource Usage Summary: missing {name}')
  result[name]={'used':float(m[1]),'available':float(m[2]),'reported_percent':int(m[3])}
 return result

def compare(paths):
 reports=[parse_report(read_report(p)) for p in paths]
 for name in reports[0]:
  if len({r[name]['available'] for r in reports})!=1:raise ValueError(f'{name}: device capacities differ')
 lines=['# CPU size comparison','', '| Resource | T80 | eZ80 compat | eZ80 ADL | ADL minus compat | ADL / T80 |','|---|---:|---:|---:|---:|---:|']
 for name in reports[0]:
  values=[r[name]['used'] for r in reports]
  ratio=f'{values[2]/values[0]:.3f}' if values[0] else 'N/A'
  lines.append(f'| {name} | {values[0]:g} | {values[1]:g} | {values[2]:g} | {values[2]-values[1]:+g} | {ratio} |')
 lines+=['','Inputs:']+[f'- {Path(p).name}' for p in paths]
 return '\n'.join(lines)+'\n'

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('t80');parser.add_argument('compat');parser.add_argument('adl');parser.add_argument('--output')
 args=parser.parse_args()
 result=compare([args.t80,args.compat,args.adl])
 if args.output:Path(args.output).write_text(result,encoding='utf-8')
 else:print(result,end='')
