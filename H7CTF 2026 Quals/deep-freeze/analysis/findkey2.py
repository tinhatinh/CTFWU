"""Anchor on the known IV to find the adjacent AES key.

The stager calls os.urandom(32) then os.urandom(16), so the two PyBytesObjects sit
back-to-back in the heap. Locating the 16 IV bytes in the dump therefore puts the
32-byte key within a few hundred bytes, which the known-plaintext oracle confirms.

usage: python findkey.py <dump> <locked> [span-around-iv]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lime  # noqa: E402
from cryptography.hazmat.primitives import ciphers  # noqa: E402
from cryptography.hazmat.primitives.ciphers.modes import ECB  # noqa: E402

P1 = b"%PDF-1.4\n1 0 obj"


def needle_hits(secs, path, needle):
    f = open(path, "rb")
    total = sum(e - s + 1 for _i, s, e, _t, _d in secs)
    hits = []
    CHUNK = 1 << 26
    carried = b""
    off = 0
    while off < total:
        f.seek(off)
        buf = f.read(CHUNK)
        if not buf:
            break
        data = carried + buf
        base = off - len(carried)
        start = 0
        while True:
            i = data.find(needle, start)
            if i < 0:
                break
            hits.append(base + i)
            start = i + 1
        carried = data[-(len(needle) - 1):]
        off += len(buf)
    f.close()
    return hits


def main():
    dump, locked = sys.argv[1], sys.argv[2]
    span = int(sys.argv[3]) if len(sys.argv) > 3 else 512

    blob = open(locked, "rb").read()
    iv, c1 = blob[:16], blob[16:32]
    want = bytes(a ^ b for a, b in zip(P1, iv))
    print(f"[*] IV={iv.hex()} C1={c1.hex()}")

    secs = lime.sections(dump)
    hits = needle_hits(secs, dump, iv)
    print(f"[*] IV located {len(hits)} time(s): " + ", ".join(f"0x{h:x}" for h in hits[:12]))

    f = open(dump, "rb")
    tested = 0
    for h in hits:
        lo = max(0, h - span)
        f.seek(lo)
        win = f.read(2 * span)
        for k in range(len(win) - 32):
            key = win[k:k + 32]
            tested += 1
            c = ciphers.Cipher(ciphers.algorithms.AES(key), ECB())
            if c.decryptor().update(c1) == want:
                va = lime.vaddr_of(secs, lo + k)
                dist = lo + k - h
                print(f"[+] KEY at vaddr 0x{va:x} (file 0x{lo + k:x}), {dist:+d} bytes from the IV object")
                print(f"    key = {key.hex()}")
                print(f"    tested {tested} candidate windows")
                return 0
    print(f"[-] no key within {span} B of the IV ({tested} windows)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
