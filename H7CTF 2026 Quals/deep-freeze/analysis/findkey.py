"""Recover the AES-256 key from the LiME dump using a known-plaintext oracle.

The .locked file is IV(16) || AES-256-CBC(PKCS7(pdf)). The plaintext head is known
("%PDF-1.4\n1 0 obj"), so for any 32-byte window K in memory:

    D_K(C1) == P1 XOR IV      <=>      K is the key

Only cheap single-block ECB decryptions are done, and candidates come from windows
around the stager's heap marker string.

usage: python findkey.py <dump> <locked> [needle]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lime  # noqa: E402
from cryptography.hazmat.primitives import ciphers  # noqa: E402
from cryptography.hazmat.primitives.ciphers.modes import ECB  # noqa: E402

P1 = b"%PDF-1.4\n1 0 obj"


def load_locked(path):
    blob = open(path, "rb").read()
    return blob[:16], blob[16:32], blob


def regions(secs, path, needle, span):
    """Yield (base_file_off, bytes) for each marker hit, read once."""
    f = open(path, "rb")
    total = sum(e - s + 1 for _i, s, e, _t, _d in secs)
    hits = []
    CHUNK = 1 << 24
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
    print(f"[*] marker found {len(hits)} time(s)")
    for h in hits:
        lo = max(0, h - span)
        f.seek(lo)
        yield lo, f.read(2 * span)
    f.close()


def main():
    dump, locked = sys.argv[1], sys.argv[2]
    needle = sys.argv[3].encode() if len(sys.argv) > 3 else b"kdmp-resident-do-not-swap"
    span = int(sys.argv[4]) if len(sys.argv) > 4 else 1 << 17

    iv, c1, blob = load_locked(locked)
    want = bytes(a ^ b for a, b in zip(P1, iv))
    print(f"[*] IV={iv.hex()}  C1={c1.hex()}  target D_K(C1)={want.hex()}")

    secs = lime.sections(dump)
    tested = 0
    for base, win in regions(secs, dump, needle, span):
        for k in range(len(win) - 32):
            key = win[k:k + 32]
            tested += 1
            try:
                c = ciphers.Cipher(ciphers.algorithms.AES(key), ECB())
            except Exception:
                continue
            if c.decryptor().update(c1) == want:
                va = lime.vaddr_of(secs, base + k)
                print(f"[+] KEY FOUND  key={key.hex()}  vaddr=0x{va:x}  (tested {tested} candidates)")
                return key
    print(f"[-] no key in {tested} candidates; widen span")


if __name__ == "__main__":
    main()
