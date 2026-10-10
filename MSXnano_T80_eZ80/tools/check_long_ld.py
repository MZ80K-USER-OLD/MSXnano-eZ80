"""Check settled upper register reads against observed instruction writes."""
from pathlib import Path
import sys

def check(path):
    scopes=[]; ids={}; state={}; groups=[]; events=[]; t=0
    for line in path.read_text().splitlines():
        x=line.split()
        if line.startswith('$scope'): scopes.append(x[2])
        elif line.startswith('$upscope'): scopes.pop()
        elif line.startswith('$var'): ids[x[3]]='.'.join(scopes+[x[4]])
        elif line.startswith('#'):
            if events: groups.append((t,events))
            t=int(line[1:]);events=[]
        elif line.startswith('b') and len(x)==2: events.append((ids[x[1]],x[0][1:]))
        elif line and line[0] in '01xXzZ': events.append((ids[line[1:]],line[0]))
    if events: groups.append((t,events))
    root='tb_long_ld.dut.u0.'
    bank=[0]*8; writes=[]; checks=0
    def bit(s,name): return s.get(root+name)
    def num(s,name):
        v=bit(s,name)
        return int(v,2) if v is not None and set(v)<=set('01') else None
    for t,events in groups:
        old=state.copy(); state.update(events)
        if bit(state,'reset_n')=='0': bank=[0]*8
        elif bit(old,'clk_n')=='0' and bit(state,'clk_n')=='1' and bit(old,'clken')=='1' and bit(old,'upper_ld_we')=='1':
            addr=num(old,'regaddra[2:0]');data=num(old,'di_reg[7:0]')
            assert addr is not None and data is not None
            bank[addr]=data; writes.append((addr,data))
        for suffix in ['a','b','c']:
            addr=num(state,'regaddr'+suffix+'[2:0]');data=num(state,'regbus'+suffix+'u[7:0]')
            if addr is not None and data is not None:
                assert data==bank[addr],(path,t,suffix,addr,data,bank)
                checks+=1
    assert writes==[(0,0x56),(1,0x9A),(2,0xBC),(3,0xDE),(7,0xF0)],writes
    assert bank[2]==0xBC # short HL write must preserve stored upper path
    assert checks>100
    print(f'PASS {path.name}: five upper writes and {checks} settled upper read checks')
for path in sys.argv[1:]: check(Path(path))
