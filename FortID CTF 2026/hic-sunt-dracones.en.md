---
title: "Hic Sunt Dracones"
category: "Crypto"
tags: ["elliptic-curve", "koblitz-encoding", "dragon-curve", "gcd-elimination", "state-reuse"]
solve_date: "2026-10-10"
language: "en"
---

# Hic Sunt Dracones

**Flag:** `FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}`
**Handout:** `handout.zip` (3895 B) — `chall.py` 1658 B, `patch.py` 716 B, `output.txt` 7927 B, `Dockerfile` 455 B. Library: `github.com/awnonbhowmik/Dragon-Crypto` at commit `046ad8d`. Author: ipaljak.

## Challenge

This one ships artifacts only, no service. The `Dockerfile` builds the environment:

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && pip install --no-cache-dir pycryptodome \
    && git clone https://github.com/awnonbhowmik/Dragon-Crypto.git /opt/dragon-crypto \
    && cd /opt/dragon-crypto \
    && git checkout 046ad8d \
    && rm -rf /var/lib/apt/lists/*

COPY patch.py /tmp/patch.py
RUN python /tmp/patch.py

WORKDIR /app
COPY chall.py .

CMD ["python", "chall.py"]
```

`patch.py` replaces the library's `sq_root_mod_n` with `pow(n, (p+1)//4, p)` and changes the signature `koblitz_encoder(plainText, elliptic_a, elliptic_b)` to take an extra `p` argument (removing the hard-coded `p = 751` line). The only thing handed out is `output.txt` (7926 characters after stripping), in the format `X<x>X<x>...XY<y><Y>...Y`:

```text
X1401X35585610297891858588915664867994857255985X2282X-35585610297891858588915664867994857251439X1461X3558561029789185858
```

## Analysis

### How the encryption works

`chall.py` builds a headless turtle and assigns it into the `dragon` module **once**:

```python
class HeadlessTurtle:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.heading = 0

    def penup(self): pass
    def pendown(self): pass
    def pencolor(self, _): pass

    def goto(self, x, y):
        self.x, self.y = x, y

    def left(self, angle):
        self.heading += angle

    def right(self, angle):
        self.heading -= angle

    def forward(self, distance):
        heading = self.heading % 360
        if heading == 0:
            self.x += distance
        elif heading == 90:
            self.y += distance
        elif heading == 180:
            self.x -= distance
        else:
            self.y -= distance

    def xcor(self): return self.x
    def ycor(self): return self.y


dragon.ob = HeadlessTurtle()
flag = open("flag.txt").read().strip()
```

and the rest of `chall.py`:

```python
while True:
    p = getPrime(256, randfunc=get_random_bytes)
    if p % 4 != 3:
        continue

    a = random.randrange(1 << 255, p)
    b = random.randrange(1 << 255, p)
    if (4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p == 0:
        continue

    points = koblitz_encoder(flag, a, b, p)
    if len(points) == len(flag):
        break

private_key = (
    random.randrange(1 << 127, 1 << 128),
    random.randrange(10, 15),
    random.randrange(2) * 180,
    a,
    b,
)

encrypted = [dragon.dragon_render(point, private_key) for point in points]
print(dragon.point_to_character(encrypted))
```

`koblitz_encoder` (patched) encodes each character into the x-coordinate of a point on `y^2 = x^3 + a x + b (mod p)`:

```python
def koblitz_encoder(plainText, elliptic_a, elliptic_b, p):
    ord_lst = [ord(ch) for ch in plainText]
    k = 20

    x_coords = []
    y_coords = []
    encoded_points = []

    for m in ord_lst:
        for j in range(1, k):
            x_m = m*k+j
            n = pow(x_m, 3) + elliptic_a * x_m + elliptic_b
            y_m = sq_root_mod_n(n, p)
            if (y_m != 0):
                x_coords.append(x_m)
                y_coords.append(y_m)
                encoded_points.append((x_m, y_m))
                break
    ...
```

So `x_m = ord(c)*20 + j` with `1 <= j <= 19`, i.e. `ord(c) = x_m // 20`: recovering `x_m` is recovering the character.

`dragon_render` does nothing to the coordinates beyond translating them:

```python
def dragon_render(starting_point, private_key):
    size = private_key[0]

    x_start = starting_point[0]
    y_start = starting_point[1]
    angle = private_key[2]

    ob.penup()
    ob.goto(x_start, y_start)
    ob.pendown()

    ob.left(angle)

    steps = turn_sequence_generator(private_key)
    steps = steps[:-1]
    ob.pencolor('green')
    for i in steps:
        if i == 'f':
            ob.forward(size)
        elif i == 'r':
            ob.right(90)
        elif i == 'l':
            ob.left(90)

    x_end = round(ob.xcor())
    y_end = round(ob.ycor())

    return (x_end,y_end)
```

### The bug

`goto()` only assigns `x`, `y`; it never touches `heading`. Because `dragon.ob` is created once for all 78 points, the heading survives between calls, so the translation vector of the dragon sequence (magnitude `M`, direction set by the current heading) rotates after every point. The data in `output.txt` shows a period of 4:

```text
len(xs) 78 len(ys) 78
small 39 idx mod4 [0, 2]
big 39 idx mod4 [1, 3] signs [(1, True), (3, False)]
digit lens x: [3, 4, 41]
digit lens y: [76, 77]

  0 mod4=0 1401 char='F'
  1 mod4=1 35585610297891858588915664867994857255985 
  2 mod4=2 2282 char='r'
  3 mod4=3 -35585610297891858588915664867994857251439 
  4 mod4=0 1461 char='I'
  5 mod4=1 35585610297891858588915664867994857255122 
  6 mod4=2 2463 char='{'
  7 mod4=3 -35585610297891858588915664867994857252779 
  8 mod4=0 2042 char='f'
  9 mod4=1 35585610297891858588915664867994857255661 
 10 mod4=2 1362 char='D'
 11 mod4=3 -35585610297891858588915664867994857252799 
 12 mod4=0 2204 char='n'
 13 mod4=1 35585610297891858588915664867994857255661 
```

The 39 small x-coordinates (3-4 digits) sit exactly at `i % 4 in {0, 2}`: those are raw `x_m` values, readable as characters directly through `x_m // 20`. The other 39 have 41 digits, positive at `i % 4 == 1` and negative at `i % 4 == 3`, i.e. `x_m + M` and `x_m - M`. In other words the per-index render offsets are `(0,-M), (+M,0), (0,+M), (-M,0)` — the heading advances by 90° after each render, and `M` is the magnitude of the 14-iteration dragon sequence's net translation.

### Pinning `M`

The x-axis alone is not enough. `solve.py` turns the constraint "every `x_m` must be a printable ASCII code" into an interval for `M`:

```python
from collections import Counter

data = open("dracones_extract/output.txt").read().strip()
xpart, ypart = data.split("XY")
xs = [int(t) for t in xpart.split("X") if t]
ys = [int(t) for t in ypart.split("Y") if t]
n = len(xs)

LO, HI = 32 * 20 + 1, 126 * 20 + 19  # printable ASCII x_m range

# i%4==1 -> x = x_m + M ; i%4==3 -> x = x_m - M
lo = hi = None
for i, x in enumerate(xs):
    if i % 4 == 1:
        a, b = x - HI, x - LO
    elif i % 4 == 3:
        a, b = -x + LO, -x + HI
    else:
        continue
    lo = a if lo is None else max(lo, a)
    hi = b if hi is None else min(hi, b)

print("M window:", lo, "..", hi, "size", hi - lo + 1)


def decode(M):
    out = []
    for i, x in enumerate(xs):
        if i % 4 == 1:
            xm = x - M
        elif i % 4 == 3:
            xm = x + M
        else:
            xm = x
        m, j = divmod(xm, 20)
        if not (1 <= j <= 19 and 32 <= m <= 126):
            return None
        out.append(chr(m))
    return "".join(out)


cands = [M for M in range(lo, hi + 1) if decode(M)]
print("valid M count:", len(cands))
for M in cands[:20]:
    print(M)
    print(decode(M))

# cross-check M against y-differences (y_m +- M)
yset = set(ys)
hits = []
for M in cands:
    k = sum(1 for y in ys if (y + M) in yset or (y - M) in yset)
    hits.append((k, M))
print("y-diff support:", sorted(hits, reverse=True)[:5])
```

```text
M window: 35585610297891858588915664867994857253722 .. 35585610297891858588915664867994857253978 size 257
valid M count: 155
35585610297891858588915664867994857253724
FqrrIE{/f`D.n`Klu8h]H5s]1u_.n`tf3`W2lm_Rh4n]18_Ku67]B4_E01d]F1r]Csynt1_p1hhr?~
35585610297891858588915664867994857253726
FprrIE{/f`D.n`Klu8h]H5s]1u_.n`tf3`W2lm_Rh4n]18_Ku67]B4_E01d]F1r]Csynt1_p1hhr?~
[... 18 more candidates elided ...]
y-diff support: [(52, 35585610297891858588915664867994857253760), (0, 35585610297891858588915664867994857253975), (0, 35585610297891858588915664867994857253974), (0, 35585610297891858588915664867994857253973), (0, 35585610297891858588915664867994857253972)]
```

The script prints the first 20 candidates; the block above keeps the first two and the summary line. 155 of the 257 values in the `M` window yield a fully printable 78-character string, but only one of them is supported by the y-axis: 52 pairs of y-coordinates differ by exactly `±M`, while every other candidate scores 0.

The reason is the same heading bug. Two points carrying the same character share the same `(x_m, y_m)`; if those two points land in different `i % 4` classes, their y-coordinates differ by `±2M`. `findM.py` enumerates exactly those pairs:

```python
from collections import Counter

data = open("dracones_extract/output.txt").read().strip()
xpart, ypart = data.split("XY")
xs = [int(t) for t in xpart.split("X") if t]
ys = [int(t) for t in ypart.split("Y") if t]

even = [(i, x) for i, x in enumerate(xs) if i % 2 == 0]
print("equal-char same-class check (y must match):")
for i in range(len(even)):
    for j in range(i + 1, len(even)):
        a, b = even[i], even[j]
        if a[1] == b[1]:
            same_class = a[0] % 4 == b[0] % 4
            d = ys[b[0]] - ys[a[0]]
            print("  char %r idx %d,%d same_class=%s dy=%d" % (
                chr(a[1] // 20), a[0], b[0], same_class, d)
              + ("  -> EQUAL OK" if same_class and d == 0 else ""))

# M from cross-class same-char pairs: dy = +-2M
cands = []
for i in range(len(even)):
    for j in range(len(even)):
        if i == j:
            continue
        a, b = even[i], even[j]
        if a[1] == b[1] and a[0] % 4 != b[0] % 4:
            d = ys[b[0]] - ys[a[0]]
            if d % 2 == 0:
                cands.append(d // 2)
c = Counter(cands)
print("\nM candidates from y-pairs:", c.most_common(3))
```

```text
equal-char same-class check (y must match):
  char 'F' idx 0,60 same_class=True dy=0  -> EQUAL OK
  char 'r' idx 2,62 same_class=True dy=0  -> EQUAL OK
  char 'n' idx 12,28 same_class=True dy=0  -> EQUAL OK
  char 'n' idx 12,42 same_class=False dy=71171220595783717177831329735989714507520
  char 'u' idx 16,48 same_class=True dy=0  -> EQUAL OK
  char 'h' idx 18,40 same_class=False dy=-71171220595783717177831329735989714507520
  char 'h' idx 18,74 same_class=True dy=0  -> EQUAL OK
  char '1' idx 24,44 same_class=True dy=0  -> EQUAL OK
  char '1' idx 24,72 same_class=True dy=0  -> EQUAL OK
  char '_' idx 26,38 same_class=True dy=0  -> EQUAL OK
  char '_' idx 26,46 same_class=True dy=0  -> EQUAL OK
  char '_' idx 26,54 same_class=True dy=0  -> EQUAL OK
  char '_' idx 26,70 same_class=True dy=0  -> EQUAL OK
  char 'n' idx 28,42 same_class=False dy=71171220595783717177831329735989714507520
  char 't' idx 30,68 same_class=False dy=-71171220595783717177831329735989714507520
  char '_' idx 38,46 same_class=True dy=0  -> EQUAL OK
  char '_' idx 38,54 same_class=True dy=0  -> EQUAL OK
  char '_' idx 38,70 same_class=True dy=0  -> EQUAL OK
  char 'h' idx 40,74 same_class=False dy=71171220595783717177831329735989714507520
  char '1' idx 44,72 same_class=True dy=0  -> EQUAL OK
  char '_' idx 46,54 same_class=True dy=0  -> EQUAL OK
  char '_' idx 46,70 same_class=True dy=0  -> EQUAL OK
  char '_' idx 54,70 same_class=True dy=0  -> EQUAL OK

M candidates from y-pairs: [(35585610297891858588915664867994857253760, 5), (-35585610297891858588915664867994857253760, 5)]
```

The same-character pair `'n'` at indices 12 and 42 gives `dy = 71171220595783717177831329735989714507520 = 2M`, so `M = 35585610297891858588915664867994857253760`; all five cross-class pairs produce that same magnitude (sign depends on pair order), while every same-class pair gives `dy = 0` as the model predicts.

## Solution

With `M` known, `decode.py` recovers the whole string:

```python
data = open("dracones_extract/output.txt").read().strip()
xpart, ypart = data.split("XY")
xs = [int(t) for t in xpart.split("X") if t]
ys = [int(t) for t in ypart.split("Y") if t]
M = 35585610297891858588915664867994857253760

flag = []
for i, x in enumerate(xs):
    xm = x - M if i % 4 == 1 else (x + M if i % 4 == 3 else x)
    m, j = divmod(xm, 20)
    assert 1 <= j <= 19, (i, xm)
    flag.append(chr(m))
flag = "".join(flag)
print(flag)
print("len", len(flag))
```

```text
FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}
len 78
```

The `assert 1 <= j <= 19` never trips across the 78 points, so every recovered `x_m` has exactly the shape `ord(c)*20 + j` that `koblitz_encoder` produces.

Independent check: after removing the offsets, the 78 points must lie on one curve `y^2 = x^3 + a x + b (mod p)` with `p`, `a`, `b` still unknown. `verify_curve.py` sets `U = y^2 - x^3`, giving `U ≡ a x + b (mod p)`, and eliminates `a`, `b` with a gcd over triples of points:

```python
from math import gcd

data = open("dracones_extract/output.txt").read().strip()
xpart, ypart = data.split("XY")
xs = [int(t) for t in xpart.split("X") if t]
ys = [int(t) for t in ypart.split("Y") if t]
M = 35585610297891858588915664867994857253760

pts = []
flag = []
for i, (x, y) in enumerate(zip(xs, ys)):
    if i % 4 == 1:
        xm, ym = x - M, y
    elif i % 4 == 3:
        xm, ym = x + M, y
    elif i % 4 == 0:
        xm, ym = x, y + M
    else:
        xm, ym = x, y - M
    pts.append((xm, ym))
    flag.append(chr(xm // 20))
flag = "".join(flag)
print("flag:", flag)

# y^2 = x^3 + a*x + b (mod p)  ->  U = y^2 - x^3 = a*x + b (mod p)
U = [ (y*y - x*x*x) for x, y in pts ]

def elim(i, j, k):
    # (U_i-U_j)*(x_j-x_k) - (U_j-U_k)*(x_i-x_j) divisible by p
    return (U[i]-U[j])*(pts[j][0]-pts[k][0]) - (U[j]-U[k])*(pts[i][0]-pts[j][0])

g = 0
n = len(pts)
for i in range(n):
    for j in range(i+1, n):
        for k in range(j+1, n):
            g = gcd(g, abs(elim(i, j, k)))
            if g.bit_length() > 4000:
                break
        if g.bit_length() > 4000:
            break
    if g.bit_length() > 4000:
        break

print("gcd bit length:", g.bit_length())

def is_prime(x):
    if x < 2: return False
    for s in [2,3,5,7,11,13,17,19,23,29,31,37]:
        d = x-1; r = 0
        while d % 2 == 0: d//=2; r+=1
        t = pow(s, d, x)
        if t in (1, x-1): continue
        for _ in range(r-1):
            t = t*t % x
            if t == x-1: break
        else:
            return False
    return True

# strip small factors to isolate the 256-bit prime
q = g
for f in range(2, 1000):
    while q % f == 0:
        q //= f
print("after stripping small factors:", q.bit_length(), "prime:", is_prime(q))
p = q
print("p =", p)
print("p bits", p.bit_length(), "p%4 =", p % 4)

i, j = 0, 1
a = (U[i] - U[j]) * pow(pts[i][0] - pts[j][0], -1, p) % p
b = (U[i] - a*pts[i][0]) % p
print("a =", a)
print("b =", b)
print("check all points on curve:",
      all((y*y - (x*x*x + a*x + b)) % p == 0 for x, y in pts))
print("discriminant nonzero:", (4*a**3 + 27*b**2) % p != 0)
print("a,b in range:", 1 << 255 <= a < p, 1 << 255 <= b < p)
open("params.txt", "w").write(repr({"p": p, "a": a, "b": b, "M": M, "flag": flag}))
```

```text
flag: FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}
gcd bit length: 256
after stripping small factors: 256 prime: True
p = 71632889084998220460585926501663758252014092487587394160527445007292703874339
p bits 256 p%4 = 3
a = 67659158642535295543465736886314779748006807937709288006668440296757665214374
b = 60820608420277223246332544627179010753912164703719190958506561458000511250842
check all points on curve: True
discriminant nonzero: True
a,b in range: True True
```

All 78 de-offset points lie on the recovered 256-bit curve, `p ≡ 3 (mod 4)` matches the condition in `chall.py`, and `a`, `b` fall inside `randrange(1 << 255, p)` — the recovered model (`x_m = ord(c)*20 + j`, offsets by `i % 4`) is consistent with the challenge code itself, not merely with the readable string.

The last step re-encrypts from scratch with the pinned library. `repro.py` rewrites `turn_sequence_generator` for speed, asserts the rewrite is equivalent to the original over iterations 1..9, then searches for the `private_key`:

```python
for n in range(1, 10):
    assert fast_turn_sequence(n) == original_turn_sequence((0, n, 0, 0, 0)), n
print("turn_sequence_generator rewrite verified equivalent for iterations 1..9")

_cache = {}
dragon.turn_sequence_generator = lambda key: _cache.setdefault(
    key[1], fast_turn_sequence(key[1]))

P = 71632889084998220460585926501663758252014092487587394160527445007292703874339
A = 67659158642535295543465736886314779748006807937709288006668440296757665214374
B = 60820608420277223246332544627179010753912164703719190958506561458000511250842
M = 35585610297891858588915664867994857253760
FLAG = "FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}"
TARGET = open("dracones_extract/output.txt").read().strip()

...

points = koblitz_encoder(FLAG, A, B, P)
assert len(points) == len(FLAG)
print("koblitz points:", len(points))

found = False
for iterations, angle in itertools.product(range(10, 15), (0, 180)):
    dragon.ob = HeadlessTurtle()
    dx, dy = dragon.dragon_render((0, 0), (1, iterations, angle, A, B))
    if dx != 0 or dy == 0 or M % abs(dy):
        continue
    size = M // abs(dy)
    if not (1 << 127 <= size < 1 << 128):
        continue
    dragon.ob = HeadlessTurtle()
    enc = [dragon.dragon_render(pt, (size, iterations, angle, A, B)) for pt in points]
    out = dragon.point_to_character(enc)
    ok = out == TARGET
    print("iterations=%d angle=%-4d net_steps=%-6d size=%d (%d bits)  exact_match=%s"
          % (iterations, angle, abs(dy), size, size.bit_length(), ok))
    if ok:
        found = True
        print("\n=== output.txt reproduced byte-for-byte ===")
        print("private_key =", (size, iterations, angle, A, B))

print("\nVERIFIED" if found else "no exact reproduction found")
```

```text
turn_sequence_generator rewrite verified equivalent for iterations 1..9
koblitz points: 78
iterations=14 angle=0    net_steps=128    size=278012580452280145225903631781209822295 (128 bits)  exact_match=True

=== output.txt reproduced byte-for-byte ===
private_key = (278012580452280145225903631781209822295, 14, 0, 67659158642535295543465736886314779748006807937709288006668440296757665214374, 60820608420277223246332544627179010753912164703719190958506561458000511250842)
iterations=14 angle=180  net_steps=128    size=278012580452280145225903631781209822295 (128 bits)  exact_match=False

VERIFIED
```

`net_steps=128` also explains `M`: the 14-iteration dragon sequence has a net translation of 128 steps, each of length `size`, so `M = 128 * size` and `size = 278012580452280145225903631781209822295` sits exactly in `randrange(1 << 127, 1 << 128)`. Only `(iterations, angle) = (14, 0)` reproduces `output.txt` verbatim.

## Result

```text
FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}
```

The 78-character flag was recovered from the artifact shipped with the challenge and confirmed by reproducing `output.txt` byte-for-byte against the library at the pinned commit; the independent cross-check shows all 78 de-offset points lie on the `p`, `a`, `b` curve derived from the same data. This challenge ships no remote service. No submission response recorded.

## Reproduce

Offline challenge. You need `handout.zip` and a clone of `https://github.com/awnonbhowmik/Dragon-Crypto` at commit `046ad8d` (the `repro/` directory uses `dragon.py` and `koblitz.py` as patched by `patch.py` — the shortest route is to build the image from the handout `Dockerfile` and copy those two files out, or to apply `patch.py`'s string replacements to the clone directly).

Directory layout the scripts assume:

```text
hic/
  dracones_extract/   <- extracted from handout.zip (chall.py, patch.py, output.txt, Dockerfile)
  repro/              <- dragon.py, koblitz.py (patched, commit 046ad8d)
  solve.py, findM.py, decode.py, verify_curve.py, repro.py
```

```console
$ cd hic
$ python solve.py            # M window and the 155 candidates
$ python findM.py            # M from same-character pairs across classes
$ python decode.py           # the 78-character string
$ python verify_curve.py     # p, a, b and check all points on curve: True
$ python repro.py            # output.txt reproduced byte-for-byte
```

Save the five code blocks from the Analysis and Solution sections under those exact filenames (`solve.py`, `findM.py`, `decode.py`, `verify_curve.py`; `repro.py` additionally needs the `fast_turn_sequence`/`original_turn_sequence` definitions and the `HeadlessTurtle` class elided in the listing above). Dependencies: Python 3 standard library for all five scripts; `pycryptodome` is only needed to re-run the original `chall.py`. `verify_curve.py` writes `params.txt` containing `p`, `a`, `b`, `M`, `flag`.
