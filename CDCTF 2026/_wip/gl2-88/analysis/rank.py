import numpy as np, re, math
from collections import Counter

lam = np.load('soft_lam.npy'); rows = np.load('soft_rows.npy')
WORDS = set(w.strip().lower() for w in open('words_alpha.txt') if len(w.strip()) >= 3)
COMMON = {w for w in WORDS if len(w) >= 3}

# letter bigram model from the dictionary (proxy for English orthography)
big = Counter(); uni = Counter()
for w in WORDS:
    if len(w) > 12:
        continue
    s = w
    for a, b in zip(s, s[1:]):
        big[(a, b)] += 1; uni[a] += 1
    uni[s[-1]] += 1
TOT = sum(big.values())
L = {}
for (a, b), c in big.items():
    L[(a, b)] = math.log10((c + 0.5) / (uni[a] + 0.5 * 27))


def toks(s):
    s = re.sub(r'[^A-Za-z]', ' ', s)
    out = re.split(r'(?<=[a-z])(?=[A-Z])', s)
    return [t.lower() for t in ' '.join(out).split() if t]


def wscore(s):
    t = toks(s)
    return sum(len(x) for x in t if x in COMMON)


def bscore(s):
    x = re.sub(r'[^a-z]', '', s.lower())
    return sum(L.get((a, b), -2.5) for a, b in zip(x, x[1:])) / max(1, len(x) - 1)


flag = lambda b: 'cdctf{' + b + '}'
scored = []
for n in range(len(rows)):
    body = ''.join(chr(int(v) + 60) for v in rows[n])
    f = flag(body)
    scored.append((wscore(f), bscore(f), f, int(lam[n])))
scored.sort(key=lambda r: (-r[0], -r[1]))
with open('ranked.txt', 'w') as fh:
    for a, b, f, l in scored:
        fh.write('%d\t%.3f\t%s\t%d\n' % (a, b, f, l))
print('=== by word coverage ===')
for r in scored[:25]:
    print(r[0], round(r[1], 3), r[2])
scored.sort(key=lambda r: -r[1])
print('=== by bigram model ===')
for r in scored[:25]:
    print(round(r[1], 3), r[0], r[2])
