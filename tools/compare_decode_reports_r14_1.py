"""Compare actual GOWIN LUT counts; optionally restore R14 when LUT grows.
Use the same GOWIN version, options, constraints, device and implementation seed.
Logic percentage alone is insufficient. Timing remains a separate acceptance check.
"""
from pathlib import Path
import argparse,json,re
from select_decode_r14_1 import select

def parse_report(path):
    raw=Path(path).read_bytes()
    s=None
    for enc in ('utf-8-sig','utf-16','cp932'):
        try:
            s=raw.decode(enc);break
        except UnicodeError:pass
    if s is None:raise ValueError('Report encoding is unsupported: '+str(path))
    # GOWIN aggregate: 18065(16254 LUT, 1811 ALU, 0 ROM16).
    # Also accept an explicit LUT row, but never substitute total Logic.
    hits=re.findall(r'([0-9][0-9,]*)\s+LUT\b',s,re.I)
    if not hits:hits=re.findall(r'^\s*LUT\s*[|:]\s*([0-9][0-9,]*)',s,re.I|re.M)
    counts={int(h.replace(',','')) for h in hits}
    if len(counts)!=1:raise ValueError('Need one unambiguous actual LUT count: '+str(path))
    return {'path':str(path),'LUT':counts.pop()}

def compare(baseline,matrix,revert=False,root=None):
    b=parse_report(baseline);m=parse_report(matrix)
    delta=m['LUT']-b['LUT']
    out={'baseline':b,'matrix':m,'LUT_delta':delta,'reverted':False,'timing_review_required':True}
    if delta>0 and revert:
        if root is None:select('baseline')
        else:select('baseline',root)
        out['reverted']=True
        out['next']='Rebuild/program R14 or use a known R14 bitstream.'
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline_report',type=Path);p.add_argument('matrix_report',type=Path)
    p.add_argument('--revert-if-lut-increases',action='store_true')
    a=p.parse_args();print(json.dumps(compare(a.baseline_report,a.matrix_report,a.revert_if_lut_increases),indent=2))
