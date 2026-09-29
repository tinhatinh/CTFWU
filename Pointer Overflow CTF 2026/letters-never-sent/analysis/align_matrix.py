import itertools, math
from collections import defaultdict

CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
KEY = [ord(c) - 65 for c in "ELAPSE"]
bf = lambda c, k: (k - c) % 26

words = set(w.strip().lower() for w in open(r"C:\Tools\ctf\words_alpha.txt", encoding="utf-8", errors="ignore") if 4 <= len(w.strip()) <= 14)
qc = defaultdict(int)
tot = 0
for w in words:
    s = "    " + w + "    "
    for i in range(len(s) - 3):
        qc[s[i:i + 4]] += 1
        tot += 1
FLOOR = math.log10(0.05 / tot)
QL = {k: math.log10(v / tot) for k, v in qc.items()}


def score(s):
    t = "    " + s.lower() + "    "
    q = sum(QL.get(t[i:i + 4], FLOOR) for i in range(len(t) - 3))
    x = s.lower()
    hits = sum(1 for ln in range(4, 12) for i in range(len(x) - ln + 1) if x[i:i + ln] in words)
    return q + 25 * hits


SPECIALS = [".", "0", "{"]     # digit flag covers 0-9
best = []
for mask in itertools.product([0, 1], repeat=3):
    adv_dot, adv_digit, adv_brace = mask
    out, ki = [], 0
    for ch in CT:
        if ch.isalpha():
            out.append(chr(bf(ord(ch) - 65, KEY[ki % 6]) + 65))
            ki += 1
        elif ch == "." and adv_dot:
            out.append(ch); ki += 1
        elif ch.isdigit() and adv_digit:
            out.append(ch); ki += 1
        elif ch in "{}" and adv_brace:
            out.append(ch); ki += 1
        else:
            out.append(ch)
    s = "".join(out)
    ok = s.startswith("POCTF{")
    letters = "".join(c for c in s if c.isalpha())
    best.append((score(letters), f"dot={adv_dot} dig={adv_digit} brc={adv_brace} prefix_ok={ok}", s))

best.sort(reverse=True)
for sc, tag, s in best:
    print(f"{sc:8.1f} {tag:44s} {s}")
