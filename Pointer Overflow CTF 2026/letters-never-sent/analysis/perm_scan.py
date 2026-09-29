import itertools, math
from collections import defaultdict

CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
L = [c for c in CT if c.isalpha()]
C = [ord(c) - 65 for c in L]
KEY = [ord(c) - 65 for c in "ELAPSE"]
bf = lambda c, k: (k - c) % 26
body = C[5:]                      # 36 letters
assert len(body) == 36

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
    s = "    " + s.lower() + "    "
    q = sum(QL.get(s[i:i + 4], FLOOR) for i in range(len(s) - 3))
    t = "".join(chr(ord(a) + 32) for a in s).strip()
    hits = sum(1 for ln in range(4, 12) for i in range(len(t) - ln + 1) if t[i:i + ln] in words)
    return q + 25 * hits


def rail_decode(s, depth):
    n = len(s)
    pat, d, step = [[] for _ in range(depth)], 0, 1
    for i in range(n):
        pat[d].append(i)
        if d == depth - 1:
            step = -1
        elif d == 0:
            step = 1
        d += step
    out = [""] * n
    k = 0
    for row in pat:
        for i in row:
            out[i] = s[k]
            k += 1
    return "".join(out)


def rail_encode(s, depth):
    n = len(s)
    pat, d, step = [[] for _ in range(depth)], 0, 1
    for i in range(n):
        pat[d].append(i)
        if d == depth - 1:
            step = -1
        elif d == 0:
            step = 1
        d += step
    return "".join(s[i] for row in pat for i in row)


DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def spiral(grid, n, outward=False, ccw=False):
    order = []
    r = c = 0
    seen = set()
    d = 0
    for _ in range(n * n):
        order.append((r, c))
        seen.add((r, c))
        for step in range(4):
            nd = (d + (step if not ccw else -step)) % 4
            nr, nc = r + DIRS[nd][0], c + DIRS[nd][1]
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:
                r, c, d = nr, nc, nd
                break
        else:
            break
    if outward:
        order = order[::-1]
    return "".join(grid[i * n + j] for i, j in order)


def to_grid(s, n=6, colmajor=False):
    g = list(s)
    if colmajor:
        g = [s[c * n + r] for r in range(n) for c in range(n)]
    return g


def letters_to_str(xs):
    return "".join(chr(x + 65) for x in xs)


plain_bf = letters_to_str([bf(c, KEY[(5 + i) % 6]) for i, c in enumerate(body)])
plain_bf0 = letters_to_str([bf(c, KEY[i % 6]) for i, c in enumerate(body)])
print("beaufort body (stream cont.):", plain_bf)
print("beaufort body (key restart) :", plain_bf0)

cands = []
for name, src in (("after-bf", plain_bf), ("cipher", letters_to_str(body))):
    for d in range(2, 13):
        for fn, tag in ((rail_decode, "raildec"), (rail_encode, "railenc")):
            t = fn(src, d)
            v = t if name == "after-bf" else letters_to_str([bf(ord(ch) - 65, KEY[(5 + i) % 6]) + 65 for i, ch in enumerate(t)])
            cands.append((score(v), f"{name}/{tag}{d}", v))
    for n in (6,):
        for cm in (False, True):
            g = to_grid(src, n, cm)
            for outw in (False, True):
                for ccw in (False, True):
                    t = spiral(g, n, outw, ccw)
                    v = t if name == "after-bf" else letters_to_str([bf(ord(ch) - 65, KEY[(5 + i) % 6]) + 65 for i, ch in enumerate(t)])
                    cands.append((score(v), f"{name}/spiral{'-out' if outw else ''}{'-ccw' if ccw else ''}{'-cm' if cm else ''}", v))
    t = "".join(src[i * 6 + j] if (i * 6 + j) < len(src) else "" for j in range(6) for i in range(6))
    v = t if name == "after-bf" else letters_to_str([bf(ord(ch) - 65, KEY[(5 + i) % 6]) + 65 for i, ch in enumerate(t)])
    cands.append((score(v), f"{name}/grid-transpose", v))

cands.sort(key=lambda x: -x[0])
print("\ntop candidates:")
for sc, tag, v in cands[:12]:
    print(f"  {sc:8.1f} {tag:26s} {v}")
