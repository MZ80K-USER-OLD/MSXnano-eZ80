"""Usage: python decode_wait_snapshot_r22_3.py 5 0 C 0 0 0 1 0 1 0 0 0 1 0 5 E
Supply 16 hex digits read from LED pages 0..F, in that order (least-significant first).
"""
import sys,json
digits=''.join(sys.argv[1:]).replace(' ','').replace(',','').upper()
if len(digits)!=16 or any(c not in '0123456789ABCDEF' for c in digits):
 raise SystemExit('Specify 16 hex digits in page order 0..F (not normal hex address order).')
x=sum(int(c,16)<<(4*i)for i,c in enumerate(digits))
bit=lambda n:(x>>n)&1
print(json.dumps(dict(snapshot=f'{x:016X}',state=['IDLE','WAIT_RAM','COMPLETE','DRAIN'][x&3],ram_req=bit(2),ram_done=bit(3),ram_write=bit(4),ext_wait_n=bit(5),done_meta=bit(6),done_sync=bit(7),cpu_mreq_n=bit(8),cpu_rd_n=bit(9),cpu_wr_n=bit(10),extended_window=bit(11),controller_running=bit(12),controller_selected=bit(13),controller_pending=bit(14),controller_sync=bit(15),cpu_addr=f'{(x>>16)&0xffffff:06X}',held_ram_addr=f'{(x>>40)&0x7fffff:06X}',wait_io=bit(63)),indent=2))
