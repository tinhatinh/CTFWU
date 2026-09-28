"""Thu thap vector MINT de tai tao khoa ky offline.

Muc tieu: neu stamp = XOR/accumulate cua bang tra theo (vi tri, byte) thi chi can
16 x 256 cau hinh la tai duoc toan bo bang, va ta tu mint duoc ma khong can dich.
Doc kieu kien: tra ve ngay khi gap '\n' (khong cho timeout), vi 4600 cau hinh ma
moi cau cho 0.6s la vuot qua thoi gian con lai cua instance.
"""
import binascii
import os
import socket
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, PORT = "pwn.h7tex.com", 43708
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mint_vectors.txt")


class Svc:
    def __init__(self, host=HOST, port=PORT):
        self.s = socket.create_connection((HOST, PORT), timeout=25)
        self.buf = b""
        self.s.settimeout(6.0)

    def line(self, cmd):
        """Gui mot lenh va tra ve dong phan hoi dau tien, ngay khi no den."""
        if cmd is not None:
            self.s.sendall(cmd.encode() + b"\n")
        while b"\n" not in self.buf:
            c = self.s.recv(65536)
            if not c:
                raise EOFError("lost at %r" % (cmd or "")[:40])
            self.buf += c
        i = self.buf.index(b"\n")
        out, self.buf = self.buf[:i], self.buf[i + 1:]
        return out.decode(errors="replace").strip()

    def mint(self, data):
        return self.line("MINT " + binascii.hexlify(data).decode())


def main(limit=None):
    v = Svc()
    print("[*] banner:", v.line(None))
    print("[*] nonce:", v.line("NONCE"))
    t0 = time.time()
    n = 0
    with open(OUT, "a", encoding="utf-8") as f:
        def put(inp):
            nonlocal n
            if limit and n >= limit:
                raise StopIteration
            out = v.mint(inp)
            f.write("%s %s\n" % (binascii.hexlify(inp).decode() or "-", out))
            n += 1

        def onehot(p, b):
            x = bytearray(16)
            x[p] = b
            return bytes(x)

        blocks = []
        blocks.append(("len1", [bytes([b]) for b in range(256)]))
        blocks.append(("pos", [onehot(p, b) for p in range(16) for b in range(256)]))
        blocks.append(("lens", [bytes(L) for L in range(0, 17)]
                       + [b"\xff" * L for L in range(0, 17)]))
        for name, items in blocks:
            try:
                for x in items:
                    put(x)
            except StopIteration:
                break
            f.flush()
            print("[*] %s: %d vec, %.0fs" % (name, n, time.time() - t0))
        f.flush()
    print("[+] %d vector / %.0fs -> %s" % (n, time.time() - t0, OUT))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
