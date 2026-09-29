import itertools, math
from collections import defaultdict

CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
IDX = [i for i, ch in enumerate(CT) if ch.isalpha()]
C = [ord(CT[i]) - 65 for i in IDX]
N = len(C)
FIX = [ord(c) - 65 for c in "ELAPS"]

words = [w.strip().lower() for w in open(r"C:\Tools\ctf\words_alpha.txt", encoding="utf-8", errors="ignore") if 3 <= len(w.strip()) <= 16]
qc = defaultdict(int)
tot = 0
for w in words:
    s = "    " + w + "    "
    for i in range(len(s) - 3):
        qc[s[i:i + 4]] += 1
        tot += 1
WSET = set(words)
FLOOR = math.log10(0.05 / tot)
QL = {k: math.log10(v / tot) for k, v in qc.items()}


def qscore(letters):
    s = "    " + "".join(chr(c + 97) for c in letters) + "    "
    return sum(QL.get(s[i:i + 4], FLOOR) for i in range(len(s) - 3))


def wordhit(letters):
    s = "".join(chr(c + 65) for c in letters).lower()
    return sum(1 for ln in range(4, 12) for i in range(len(s) - ln + 1) if s[i:i + ln] in WSET)


print("period  best_key                       qscore   words   plaintext")
for P in range(6, 10):
    best = None
    for combo in itertools.product(range(26), repeat=P - 5):
        key = FIX + list(combo)
        pt = [(key[i % P] - C[i]) % 26 for i in range(N)]
        sc = qscore(pt)
        if best is None or sc > best[0]:
            best = (sc, key, pt)
    sc, key, pt = best
    print(f"{P:5d}  {''.join(chr(k+65) for k in key):28s} {sc:7.1f} {wordhit(pt):6d}   "
          f"{''.join(chr(c+65) for c in pt)}")
