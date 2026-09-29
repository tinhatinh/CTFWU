import itertools

CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
L = [c for c in CT if c.isalpha()]
C = [ord(c) - 65 for c in L]
KEY = [ord(c) - 65 for c in "ELAPSE"]
bf = lambda c, k: (k - c) % 26

body_c = C[5:]                      # 36 letters after POCTF
assert len(body_c) == 36, len(body_c)
body_bf = "".join(chr(bf(c, KEY[(5 + i) % 6]) + 65) for i, c in enumerate(body_c))
print("beaufort body:", body_bf)

words = set()
for w in open(r"C:\Tools\ctf\words_alpha.txt", encoding="utf-8", errors="ignore"):
    w = w.strip().lower()
    if 3 <= len(w) <= 14:
        words.add(w)
LEET = {"0": "O", "1": "I", "2": "Z", "3": "E", "4": "A", "5": "S", "6": "G", "7": "T", "8": "B", "9": "G"}


def unleet(s):
    return "".join(LEET.get(ch, ch) for ch in s).lower()


def score(s):
    s = s.lower()
    tot, i = 0, 0
    while i < len(s):
        for ln in range(9, 2, -1):
            if s[i:i + ln] in words:
                tot += ln * ln
                i += ln
                break
        else:
            i += 1
    return tot


def grid_perms(s, n=6):
    rows = [s[i:i + n] for i in range(0, len(s), n)]
    for perm in itertools.permutations(range(n)):
        tag = "".join(map(str, perm))
        yield tag, "".join("".join(r[p] for r in rows) for p in perm)
        yield "c" + tag, "".join("".join(rows[r][c] for r in range(len(rows))) for c in perm)


cands = []
# A: beaufort first, then transposition
for perm, cand in grid_perms(body_bf):
    cands.append((score(cand) + score(unleet(cand)), "bf->transpose", perm, cand))
# B: transposition first, then beaufort
for perm, cand in grid_perms("".join(chr(c + 65) for c in body_c)):
    dec = "".join(chr(bf(ord(ch) - 65, KEY[(5 + i) % 6]) + 65) for i, ch in enumerate(cand))
    cands.append((score(dec) + score(unleet(dec)), "transpose->bf", perm, dec))

cands.sort(key=lambda x: -x[0])
print("best of", len(cands))
for sc, label, perm, cand in cands[:10]:
    print(f"{sc:6d} {label:14s} perm={perm:8s} -> {cand}")
