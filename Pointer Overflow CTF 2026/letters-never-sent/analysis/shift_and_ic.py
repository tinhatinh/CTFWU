import itertools, re

CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
L = [c for c in CT if c.isalpha()]
C = [ord(c) - 65 for c in L]

words = set()
for w in open(r"C:\Tools\ctf\words_alpha.txt", encoding="utf-8", errors="ignore"):
    w = w.strip().lower()
    if 4 <= len(w) <= 14:
        words.add(w)


def score(s):
    s = s.lower()
    tot, i = 0, 0
    while i < len(s):
        for ln in range(12, 3, -1):
            if s[i:i + ln] in words:
                tot += ln * ln
                i += ln
                break
        else:
            i += 1
    return tot


print("=== single-letter Beaufort / Vigenere / variant / atbash over the whole letter stream")
res = []
for k in range(26):
    for name, f in (("beaufort", lambda c, k: (k - c) % 26),
                    ("vigenere", lambda c, k: (c - k) % 26),
                    ("variant", lambda c, k: (c + k) % 26),
                    ("atbash+shift", lambda c, k: (25 - c + k) % 26)):
        s = "".join(chr(f(c, k) + 65) for c in C)
        res.append((score(s), name, k, s))
res.sort(reverse=True)
for sc, name, k, s in res[:6]:
    print(f"  {sc:6d} {name:12s} k={chr(65+k)} -> {s}")

print("\n=== bigram-frequency column analysis: index of coincidence per period")


def ic(seq):
    from collections import Counter
    n = len(seq)
    if n < 2:
        return 0
    c = Counter(seq)
    return sum(v * (v - 1) for v in c.values()) / (n * (n - 1))


for p in range(1, 15):
    cols = [C[i::p] for i in range(p)]
    print(f"  period {p:2d} mean IC={sum(ic(col) for col in cols)/len(cols):.4f}")
