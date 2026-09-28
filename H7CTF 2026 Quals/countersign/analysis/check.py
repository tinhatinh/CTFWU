import binascii
import socket
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, PORT = "pwn.h7tex.com", 43708
SAVED_NONCE = "81c7ad957a5c8aa9"


class C:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=20)
        self.buf = b""

    def readline(self, t=8.0):
        self.s.settimeout(t)
        while b"\n" not in self.buf:
            c = self.s.recv(65536)
            if not c:
                raise EOFError
            self.buf += c
        i = self.buf.index(b"\n")
        out, self.buf = self.buf[:i], self.buf[i + 1:]
        return out.decode(errors="replace").strip()

    def cmd(self, line):
        self.s.sendall(line.encode() + b"\n")
        return self.readline()


def x(*bs):
    r = bs[0]
    for b in bs[1:]:
        r = bytes(x ^ y for x, y in zip(r, b))
    return r


c = C()
print("banner1:", c.readline())
print("banner2:", c.readline())
n = c.cmd("NONCE")
print("nonce now:", n, " saved:", SAVED_NONCE, " SAME" if n == SAVED_NONCE else " *** CHANGED (instance rebooted) ***")

# do dai stamp theo do dai input
print("\n== stamp length vs input length ==")
for L in (0, 1, 2, 3, 8, 15, 16):
    m = bytes(range(L))
    r = c.cmd("MINT " + binascii.hexlify(m).decode())
    print("  in %2d -> %2d byte out: %s" % (L, len(r) // 2, r))

# cong tinh XOR tren block 16 byte
print("\n== XOR additivity on 16-byte blocks ==")
A = bytes([0x41]) + bytes(15)
B = bytes([0, 0x41]) + bytes(14)
Z = bytes(16)
AB = bytes([0x41, 0x41]) + bytes(14)
st = {}
for name, m in (("Z", Z), ("A", A), ("B", B), ("AB", AB)):
    r = c.cmd("MINT " + binascii.hexlify(m).decode())
    st[name] = binascii.unhexlify(r.encode())
    print("  %-2s %s -> %s" % (name, binascii.hexlify(m).decode(), r))
for k in st:
    print("  len(stamp %s) = %d" % (k, len(st[k])))
try:
    pred = x(st["A"], st["B"], st["Z"])
    print("  du doan AB = %s   thuc te = %s   -> %s"
          % (pred.hex(), st["AB"].hex(), "CONG TINE" if pred == st["AB"] else "khong cong"))
except Exception as e:
    print("  so sanh khong thuc hien duoc:", e)

c.s.close()
