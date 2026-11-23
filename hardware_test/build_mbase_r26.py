"""R26 MBASE regression uses the new window semantics; the R12 COM is archived."""
from pathlib import Path
r=Path(__file__).resolve().parent
s=(r/'build_window_r26.py').read_text().replace('EZ80WIN','EZ80MB')
exec(compile(s,str(r/'build_window_r26.py'),'exec'),{'__file__':__file__})
