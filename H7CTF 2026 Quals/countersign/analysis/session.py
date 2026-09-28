"""Ket noi den aria... a, toi den countersign core: gi MOT ket noi cho ca phien.

Image va khoa la per-connection, nen moi thu (GET -> giai -> MINT -> RUN) phai dien
ra tren cung mot socket.  Core in tung byte hex voi stdout _IONBF (~53 KB/s) nen GET
~145 KB mat ~3 giay: doc den khi im lang, khong cat bang timeout ngan.
"""
import binascii
import os
import socket
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST, PORT = "pwn.h7tex.com", 43708
HERE = os.path.dirname(os.path.abspath(__file__))
RECL, HDR = 720, 0x20          # byte/record da serialize, header


class Core:
    def __init__(self, host=HOST, port=PORT):
        self.s = socket.create_connection((host, port), timeout=40)
        self.s.settimeout(20.0)
        self.buf = b""
        self.lines = []
        banner = []
        while len(banner) < 2:
            self._fill()
            banner = [l for l in self.lines if l]
        self.banner = banner
        self.lines = []          # banner KHONG duoc de lai trong hang doi phan hoi
        self.nonce = None
        self.image = None

    def _fill(self, t=20.0):
        self.s.settimeout(t)
        c = self.s.recv(1 << 18)
        if not c:
            raise EOFError("connection closed")
        self.buf += c
        while b"\n" in self.buf:
            i = self.buf.index(b"\n")
            self.lines.append(self.buf[:i].decode(errors="replace").strip())
            self.buf = self.buf[i + 1:]

    def line(self, cmd=None, t=20.0):
        if cmd is not None:
            self.s.sendall(cmd.encode() + b"\n")
        while not self.lines:
            self._fill(t)
        return self.lines.pop(0)

    def get_nonce(self):
        self.nonce = self.line("NONCE")
        return self.nonce

    def get_image(self, idle=1.5, save="image.bin"):
        """GET: doc het stream hex.  Luu y: toan bo hex nam tren MOT ket thuc bang
        '\\n', nen phai lay chuoi hex dai nhat trong toan bo noi dung, khong dung
        'phan con lai sau dong cuoi' (se ra rong)."""
        self.s.sendall(b"GET\n")
        got = b""
        self.s.settimeout(idle + 8)
        while True:
            try:
                c = self.s.recv(1 << 18)
            except (socket.timeout, TimeoutError):
                break
            except Exception:
                break
            if not c:
                break
            got += c
        best = b""
        run = b""
        for ch in got:
            if chr(ch) in "0123456789abcdefABCDEF":
                run += bytes([ch])
                if len(run) > len(best):
                    best = run
            else:
                run = b""
        if len(best) % 2:
            best = best[:-1]
        self.image = binascii.unhexlify(best)
        self.raw_get = got
        if save:
            open(os.path.join(HERE, save), "wb").write(self.image)
        return self.image

    def mint(self, data):
        return self.line("MINT " + binascii.hexlify(data).decode())

    def run(self, data24):
        assert len(data24) == 24, len(data24)
        return self.line("RUN " + binascii.hexlify(data24).decode())

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def records(img):
    """cat 199 record 720 byte -> dict theo layout serialized."""
    n = (len(img) - HDR) // RECL
    out = []
    for i in range(n):
        r = img[HDR + i * RECL: HDR + (i + 1) * RECL]
        rid, ln = struct_u16(r, 0), struct_u16(r, 2)
        out.append(dict(i=i, id=rid, ln=ln, pre=r[4:13], code=r[13:13 + ln],
                        tail=r[13 + ln:]))
    return out


def struct_u16(b, o):
    return b[o] | (b[o + 1] << 8)


if __name__ == "__main__":
    c = Core()
    print("[*] banner:", c.banner)
    print("[*] nonce:", c.get_nonce())
    img = c.get_image()
    print("[*] image %d byte  magic %s  nonce@0x0a %s"
          % (len(img), img[:4], img[0x0a:0x12].hex()))
    recs = records(img)
    print("[*] records:", len(recs))
    for r in recs[:6]:
        print("    id=%d ln=%d code[:8]=%s" % (r["id"], r["ln"], r["code"][:8].hex()))
    lns = sorted({r["ln"] for r in recs})
    print("[*] code_len values:", lns[:12], "..." if len(lns) > 12 else "")
    print("[*] ids dau:", [r["id"] for r in recs[:20]])
    print("[*] mint empty:", c.mint(b""))
    c.close()
