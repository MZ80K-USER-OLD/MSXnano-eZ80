from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent.parent
work=root/'verification_size'
for variant in ['T80','eZ80_compat','eZ80_ADL']:
 project=root/'fpga'/('project_size_'+variant)/('CPU_Size_'+variant+'.gprj')
 cwd=work/variant;cwd.mkdir(parents=True,exist_ok=True)
 for f in ET.parse(project).findall('./FileList/File'):
  source=(project.parent/f.attrib['path']).resolve()
  if not source.is_file():raise RuntimeError(f'Missing project file: {source}')
  if f.attrib['type']=='file.vhdl':subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(source)],cwd=cwd,check=True)
 subprocess.run(['ghdl','-a','--std=08','-fsynopsys',str(root/'sim/tb_cpu_size.vhd')],cwd=cwd,check=True)
 for wait in ['false','true']:
  print(f'CASE {variant} WAIT={wait}',flush=True)
  subprocess.run(['ghdl','-r','--std=08','-fsynopsys','tb_cpu_size',f'-gWIDE={str(variant=="eZ80_ADL").lower()}',f'-gINSERT_WAIT={wait}','--assert-level=error'],cwd=cwd,check=True)
print('PASS all six CPU-size wrapper cases',flush=True)
