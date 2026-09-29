import random
from collections import defaultdict

CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
LET = [i for i, ch in enumerate(CT) if ch.isalpha()]
C = [ord(CT[i]) - 65 for i in LET]
N = len(C)
FIX = [ord(x) - 65 for x in "ELAPS"]

words = [w.strip().lower() for w in open(r"C:\Tools\ctf\words_alpha.txt", encoding="utf-8", errors="ignore") if 3 <= len(w.strip()) <= 24]
WSET = set(words)

# quadgram log-probabilities from within-word n-grams
qc = defaultdict(int)
tot = 0
for w in words:
    s = "   " + w + "   "
    for i in range(len(s) - 3):
        qc[s[i:i + 4]] += 1
        tot += 1
import math
QL = {k: math.log10(v / tot) for k, v in qc.items()}
FLOOR = math.log10(0.01 / tot)


def qscore(s):
    s = "   " + s + "   "
    return sum(QL.get(s[i:i + 4], FLOOR) for i in range(len(s) - 3))


def decrypt(key):
    return "".join(chr((key[i % len(key)] - C[i]) % 26 + 65) for i in range(N))


def runs_of(plain):
    return [r for r in plain if r]


def score(plain):
    s = qscore(plain.lower())
    bonus = 0
    for r in runs_of(plain):
        if len(r) >= 4:
            if r.lower() in WSET:
                bonus += 30
            else:  # leet-flavoured: check with common digit substitutions reversed
                for a, b in (("0", "O"), ("1", "I"), ("3", "E"), ("4", "A"), ("5", "S"), ("7", "T"), ("6", "G"), ("2", "Z")):
                    r = r.replace(b, a)
            if r.lower() in WSET:
                bonus += 40
    return s + bonus


best_overall = None
for period in range(5, 17):
    key = FIX + [random.randrange(26) for _ in range(period - 5)]
    cur = score(decrypt(key))
    improved = True
    while improved:
        improved = False
        for pos in range(5, period):
            base = key[pos]
            for cand in range(26):
                if cand == base:
                    continue
                key[pos] = cand
                sc = score(decrypt(key))
                if sc > cur:
                    cur, base, improved = sc, cand, True
                else:
                    key[pos] = base
            key[pos] = base
    plain = decrypt(key)
    print(f"P={period:2d} score={cur:8.1f} key={''.join(chr(k+65) for k in key)} pt={plain}")
    if best_overall is None or cur > best_overall[0]:
        best_overall = (cur, period, key, plain)

print("\nBEST:", best_overall[2], "".join(chr(k + 65) for k in best_overall[2]))
print("plain:", best_overall[3])
