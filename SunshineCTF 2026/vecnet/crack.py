#!/usr/bin/env python
"""Turn the requirement sentence into a keyed search.

vec2text returned: "The user's first and last initials, three special characters followed by the
magic string."  The other two rows supply the rest: the magic string is `sunshinectf8_`, and
`user_hash_sha256` is the natural *fast* oracle -- sha256 costs ~1us while 7zAES costs ~0.2s per
try, so the structure is searched against the hash and only the surviving candidate is handed to
7z.  The letters and the three symbols are the only unknowns.
"""
import hashlib, itertools, string, sys
from multiprocessing import Pool
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

TARGET = "d8dd241199d2617765d7613fdd1df5358297b55f258647fe463de586bbfe3ebf"
MAGIC = "sunshinectf8_"
PUNCT = "".join(c for c in string.punctuation)          # 32 chars
LETTERS = string.ascii_lowercase

def forms(pair):
    a, b = pair
    return {pair, pair.upper(), a.upper() + b, a + b.upper()}

def gen(structure):
    for x in itertools.product(LETTERS, LETTERS):
        for ini in forms("".join(x)):
            if structure == "is":            # initials + 3 symbols + magic
                for s in itertools.product(PUNCT, repeat=3):
                    yield ini + "".join(s) + MAGIC
            elif structure == "si":          # 3 symbols + initials + magic
                for s in itertools.product(PUNCT, repeat=3):
                    yield "".join(s) + ini + MAGIC
            elif structure == "im":          # initials + magic + 3 symbols
                for s in itertools.product(PUNCT, repeat=3):
                    yield ini + MAGIC + "".join(s)

def probe(cands):
    for c in cands:
        if hashlib.sha256(c.encode()).hexdigest() == TARGET:
            return c
    return None

if __name__ == "__main__":
    quick = []
    for x in itertools.product(LETTERS, LETTERS):
        for ini in forms("".join(x)):
            for s in PUNCT:
                quick += [ini + s * 3 + MAGIC, s * 3 + ini + MAGIC, ini + MAGIC + s * 3,
                          ini + s + s + s.upper() + MAGIC]
    print("[*] cheap pass (same symbol x3): %d candidates" % len(quick), flush=True)
    with Pool(8) as p:
        CH = 200000
        res = p.map(probe, [quick[i:i + CH] for i in range(0, len(quick), CH)], chunksize=1)
    for r in res:
        if r:
            print("[+] FOUND: %r" % r)
            sys.exit(0)
    print("[-] no hit in the cheap pass", flush=True)
    total = 26 * 26 * 4 * len(PUNCT) ** 3
    print("[*] full pass: %d candidates, structure initials+3symbols+magic only first" % total, flush=True)
    jobs = [gen("is")]
    for g in jobs:
        n = 0
        with Pool(8) as p:
            for r in p.imap(probe, (list(itertools.islice(g, i, i + CH)) for i in itertools.count(0, CH)),
                            chunksize=1):
                n += CH
                if n % 4000000 < CH:
                    print("   %dM tried" % (n // 1000000), flush=True)
                if r:
                    print("[+] FOUND: %r" % r)
                    sys.exit(0)
        break
    print("[-] no hit")
