from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
commands=[['gcc','-std=gnu11','-O2','-fPIC','-shared','-Ivendor/cemu_core','tools/oracle.c','vendor/cemu_core/cpu.c','vendor/cemu_core/registers.c','-o','tools/oracle.so'],['gcc','-std=gnu11','-O2','-fPIC','-shared','-DDEBUG_SUPPORT','-Ivendor/zdis','tools/dis.c','vendor/zdis/zdis.c','-o','tools/dis.so']]
if __name__=='__main__':
 for cmd in commands: subprocess.run(cmd,cwd=ROOT,check=True)
