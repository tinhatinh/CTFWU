"""Chạy binary countersign THAT trong Unicorn.

Muc dich: lay ground truth cho hai thu
  (1) ham nap image 0x1fa0 -> doc mang record trong .bss (kca alt_id khong bao gio ra wire)
  (2) exec_program 0x1810 va emit 0x1d50 -> duoc/den theo dung machinh that.

Roi doi chieu voi emulator Python (walk2.py).  Lech o dau -> sua o do.
"""
import struct
import sys

from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_PROT_ALL, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RIP, UC_X86_REG_RSP, UC_X86_REG_RAX, \
    UC_X86_REG_RDI, UC_X86_REG_RSI, UC_X86_REG_RDX, UC_X86_REG_RCX, UC_X86_REG_R8, \
    UC_X86_REG_R9, UC_X86_REG_RBP, UC_X86_REG_RBX, UC_X86_REG_FS_BASE

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = 0
MEMSZ = 0x1000000
STACK = 0x1200000
STKSZ = 0x100000
TRAMP = 0x1100000
STOP = 0x1110000           # dia chi cac handler cua toi

SYM = {0x6000: "getenv", 0x6008: "putchar", 0x6010: "strncpy", 0x6018: "puts",
       0x6020: "stack_chk_fail", 0x6028: "printf", 0x6030: "snprintf",
       0x6038: "memset", 0x6040: "close", 0x6048: "read", 0x6050: "fgets",
       0x6058: "memcpy", 0x6060: "setvbuf", 0x6068: "open"}


class Core:
    """Moi truong chay aria, voi PLT duoc thay bang handler Python."""

    def __init__(self, path="unpacked/countersign", urandom=b"\x00" * 32, flag=b"H7CTF{test}"):
        self.raw = open(path, "rb").read()
        self.mu = Uc(UC_ARCH_X86, UC_MODE_64)
        self.mu.mem_map(BASE, MEMSZ, UC_PROT_ALL)
        self.mu.mem_write(BASE, self.raw[:0x6320])
        # .rela.dyn RELATIVE
        for off in range(0x788, 0x788 + 10 * 24, 24):
            o, info, typ, add = struct.unpack_from("<QQqQ", self.raw, off)
            self.mu.mem_write(BASE + o, struct.pack("<Q", BASE + add))
        self.seed = urandom
        self.flag = flag
        self.env = {b"FLAG": flag}
        self.log = []
        self.tramp = {}
        addr = TRAMP
        for got, name in SYM.items():
            self.tramp[addr] = name
            self.mu.mem_write(BASE + got, struct.pack("<Q", BASE + addr))
            addr += 16
        self.mu.mem_map(TRAMP, 0x10000, UC_PROT_ALL)
        self.mu.mem_map(STACK, STKSZ, UC_PROT_ALL)
        self.mu.reg_write(UC_X86_REG_RSP, STACK + STKSZ - 0x1000)
        self.mu.hook_add(UC_HOOK_CODE, self._hook, begin=TRAMP, end=TRAMP + 0x10000)
        self.heap = 0x780000
        # 0x1fa0 doc `mov rax, fs:[0x28]` (stack canary) -> can cho FS hop le
        self.tls = 0x1120000
        self.mu.mem_map(self.tls, 0x4000, UC_PROT_ALL)
        self.mu.mem_write(self.tls + 0x28, struct.pack("<Q", 0xC0FFEE0000))
        self.mu.reg_write(UC_X86_REG_FS_BASE, self.tls)

    # --- PLT handlers -------------------------------------------------
    def _rd(self, a, n):
        return bytes(self.mu.mem_read(BASE + a, n)) if a >= BASE else bytes(self.mu.mem_read(a, n))

    def _str(self, a):
        out = b""
        while True:
            c = self._rd(a, 1)
            if c == b"\x00":
                return out
            out += c
            a += 1

    def _hook(self, mu, addr, size, user):
        try:
            self._hook_i(mu, addr, size, user)
        except BaseException as e:
            import traceback, sys
            traceback.print_exc(); sys.stdout.flush()
            mu.emu_stop()

    def _hook_i(self, mu, addr, size, user):
        name = self.tramp.get(addr)
        from unicorn import x86_const as X
        r = lambda n: mu.reg_read(getattr(X, "UC_X86_REG_" + n))
        rsp = r("RSP")
        ret = struct.unpack("<Q", bytes(mu.mem_read(rsp, 8)))[0]
        mu.reg_write(UC_X86_REG_RIP, ret)
        a1, a2, a3 = r("RDI"), r("RSI"), r("RDX")
        if name == "open":
            mu.reg_write(UC_X86_REG_RAX, 3)
        elif name == "read":
            data = self.seed if a1 == 3 else b""
            n = min(a3, len(data))
            mu.mem_write(a2, data[:n] + b"\x00" * (a3 - n))
            mu.reg_write(UC_X86_REG_RAX, n)
        elif name == "close":
            mu.reg_write(UC_X86_REG_RAX, 0)
        elif name == "memset":
            mu.mem_write(a1, bytes([a2 & 0xFF]) * a3)
            mu.reg_write(UC_X86_REG_RAX, a1)
        elif name == "memcpy":
            mu.mem_write(a1, bytes(mu.mem_read(a2, a3)))
            mu.reg_write(UC_X86_REG_RAX, a1)
        elif name == "strncpy":
            s = self._str(a2)[:a3]
            mu.mem_write(a1, s + b"\x00" * (a3 - len(s)))
            mu.reg_write(UC_X86_REG_RAX, a1)
        elif name == "getenv":
            v = self.env.get(bytes(mu.mem_read(a1, 16).split(b"\x00")[0]))
            if v is None:
                mu.reg_write(UC_X86_REG_RAX, 0)
            else:
                p = self.heap
                self.heap += 0x100
                mu.mem_write(p, v + b"\x00")
                mu.reg_write(UC_X86_REG_RAX, p)
        elif name in ("printf", "puts", "snprintf", "putchar", "setvbuf",
                      "stack_chk_fail", "fgets"):
            mu.reg_write(UC_X86_REG_RAX, 0)
        else:
            raise SystemExit("unhandled import %s" % name)

    # --- entry points -------------------------------------------------
    def call(self, addr, a=None, limit=2_000_000):
        a = a or {}
        mu = self.mu
        from unicorn import x86_const as X
        rsp = STACK + STKSZ - 0x1000
        mu.reg_write(UC_X86_REG_RSP, rsp)
        mu.mem_write(rsp, struct.pack("<Q", STOP))
        mu.reg_write(UC_X86_REG_RBP, 0)
        mu.reg_write(UC_X86_REG_RAX, 0)
        for n, v in a.items():
            mu.reg_write(getattr(X, "UC_X86_REG_" + n), v)
        mu.emu_start(BASE + addr, STOP, count=limit)
        return mu.reg_read(UC_X86_REG_RAX)

    def u16(self, off):
        return struct.unpack("<H", self._rd(off, 2))[0]

    def u32(self, off):
        return struct.unpack("<I", self._rd(off, 4))[0]

    def bytes_at(self, off, n):
        return self._rd(off, n)

    def boot(self, urandom):
        self.seed = urandom
        return self.call(0x1fa0)
