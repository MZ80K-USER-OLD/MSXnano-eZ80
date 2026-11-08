"""Select a verified R14 or R14.1 Write decoder; refuses unknown user edits."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parent.parent
def select(variant,root=ROOT):
    m=json.loads((root/'doc/R14_1_DECODE_VARIANTS.json').read_text())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    target=root/m['active']
    for v in m['variants'].values():
        if digest(root/v['path'])!=v['sha256']:raise RuntimeError('Saved variant has changed; selection refused')
    if digest(target) not in {v['sha256'] for v in m['variants'].values()}:
        raise RuntimeError('Active decoder has user edits; selection refused')
    data=(root/m['variants'][variant]['path']).read_bytes()
    target.write_bytes(data)
    assert digest(target)==m['variants'][variant]['sha256']
    return variant
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('variant',choices=['baseline','matrix'])
    print('Selected '+select(p.parse_args().variant)+'. Rebuild in GOWIN before programming the FPGA.')
