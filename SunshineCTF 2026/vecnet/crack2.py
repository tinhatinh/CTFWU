#!/usr/bin/env python
"""Index-space sha256 search over the recovered password structure.

Format from the inverted embedding:  <first+last initials> <three special characters> <magic
string>.  Nothing about which initials or which symbols is stated, so the joint space is
26*26 letter pairs x 4 case forms x 32 punctuation symbols^3 = 88.6M -- trivial against a sha256
oracle, which is exactly why the author left `user_hash_sha256` in the collection next to the
requirement text.  Only a digest match is ever handed to 7z.
"""
import hashlib, itertools, string, sys
from multiprocessing import Pool
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

TARGET = bytes.fromhex("d8dd241199d2617765d7613fdd1df5358297b55f258647fe463de586bbfe3ebf")
MAGIC = "sunshinectf8_"
PUNCT = string.punctuation                     # 32 printable specials, no alnum
INI = sorted({f for ab in map("".join, itertools.product(string.ascii_lowercase, repeat=2))
              for f in (ab, ab.upper(), ab[0].upper() + ab[1], ab[0] + ab[1].upper())})
SYM = ["".join(s) for s in itertools.product(PUNCT, repeat=3)]
N = len(INI) * len(SYM)
print("[*] initials=%d symbols=%d space/structure=%d" % (len(INI), len(SYM), N), flush=True)

def block(args):
    struct, a, b = args
    d = hashlib.sha256
    if struct == "is":
        for i in range(a, b):
            ini, sym = INI[i // len(SYM)], SYM[i % len(SYM)]
            if d((ini + sym + MAGIC).encode()).digest() == TARGET:
                return ini + sym + MAGIC
    elif struct == "si":
        for i in range(a, b):
            ini, sym = INI[i // len(SYM)], SYM[i % len(SYM)]
            if d((sym + ini + MAGIC).encode()).digest() == TARGET:
                return sym + ini + MAGIC
    elif struct == "im":
        for i in range(a, b):
            ini, sym = INI[i // len(SYM)], SYM[i % len(SYM)]
            if d((ini + MAGIC + sym).encode()).digest() == TARGET:
                return ini + MAGIC + sym
    elif struct == "smi":
        for i in range(a, b):
            ini, sym = INI[i // len(SYM)], SYM[i % len(SYM)]
            if d((sym + MAGIC + ini).encode()).digest() == TARGET:
                return sym + MAGIC + ini
    return None

if __name__ == "__main__":
    CH = 100000
    for struct in ("is", "si", "im", "smi"):
        jobs = [(struct, i, min(i + CH, N)) for i in range(0, N, CH)]
        done = 0
        with Pool(8) as p:
            for r in p.imap_unordered(block, jobs, chunksize=1):
                done += 1
                if r:
                    print("[+] FOUND (%s): %r" % (struct, r), flush=True)
                    open("analysis/password.txt", "w").write(r)
                    sys.exit(0)
                if done % 200 == 0:
                    print("   %s: %d/%d blocks" % (struct, done, len(jobs)), flush=True)
        print("[-] structure %s exhausted" % struct, flush=True)
    print("[-] no match")
