---
title: "half-truths"
category: "Crypto"
tags: ["reed-solomon", "list-decoding"]
solve_date: "2026-10-11T06:25:00+07:00"
language: "en"
---

# half-truths

**Flag:** `isfcr{l1st_d3c0d1ng_p4st_th3_r4d1us}`  
**Artifacts:** `output.json` (9,749 bytes) and the generator `chall.py` (2,838 bytes, saved locally as `chall (1).py`)

| Artifact | SHA-256 |
|---|---|
| `output.json` | `7da3464233e2682af604ad970e2b6ac772be68550a7e64a52209eeb933aa1879` |
| `chall.py` | `1dec1247c77dce83bb796b1fabfb5ab0db493a694fe9e23c53107d04da18e79e` |

## Challenge

"327 of my 512 friends lied to me. Reconstruct the secret anyway." Flag format `isfcr{}`.

The generator samples a degree-39 polynomial `f` over GF(2^31-1), hands out `N = 512` shares
`(i, f(i))` for `i = 1..512`, and only `T = 185` of them come back unmodified. The 327 altered
shares are replaced by uniformly random field elements that are guaranteed to differ from `f(x)`,
so the true polynomial agrees with exactly 185 received pairs. The flag is sealed with
`AES-GCM(key = SHA-256("c0,c1,...,c39"), nonce = "half-truths-")`, coefficients in decimal,
low order first. `output.json` gives `p`, `k`, `n`, `t`, the 512 shuffled `[x, y]` pairs and the
ciphertext/tag.

## Initial Analysis

Viewed as a Reed-Solomon problem, the honest shares form a codeword of an `[512, 40, 473]` RS code
and the received word sits at Hamming distance 327 from it. Unique decoding tolerates
`(N-K)/2 = 236` errors, i.e. it needs `T >= (N+K)/2 = 276` honest shares, so Berlekamp-Welch, Gao
and the extended-Euclidean key equation all stop short here and no error-locator/erasures variant
changes that: they are all bounded by the same minimum distance.

Two quantitative facts decide the approach:

* **List decoding applies.** The Guruswami-Sudan radius for RS codes is an agreement count of about
  `sqrt(K*N) = sqrt(20480) = 143.1`, and we hold `T = 185` agreements, so the true polynomial is
  reachable by an interpolation-and-factorisation decoder.
* **Multiplicity must be at least 2.** Sudan's original (multiplicity 1) radius is
  `sqrt(2*K*N) = 202.4 > 185`. Concretely, the multiplicity-1 parametrisation offers only
  535 monomials against 512 vanishing conditions - a borderline system - while multiplicity 2 gives
  1945 monomials against 1536 conditions, i.e. a solution space of dimension 409 to work with.

Averaging over random subsets or guessing "likely honest" shares cannot help either: a random set
of 40 shares is all-honest with probability `(185/512)^40 ~ 10^-18`, and any method that first
selects a support subset needs that subset to be more than half honest, which 36.1% cannot supply.
The whole instance has to be handled by one global linear-algebra argument.

Because we are past the unique-decoding radius, the decoder is a *list* decoder: it can in
principle return more than one polynomial. The generator's guarantee that the true `f` agrees with
*exactly* `T` shares, plus the 128-bit AES-GCM tag over the flag, is what identifies the right
candidate rather than a uniqueness proof.

## Exploitation Chain

1. **Fix the interpolation shape.** Seek `Q(x, y) = sum_{b=0}^{B} y^b Q_b(x)` with
   `deg Q_b <= D - (K-1)b`, `D = m*T - 1 = 369`, `m = 2`. Then `B = floor(369/39) = 9` and the
   degree budget per `y`-power is `369, 330, 291, 252, 213, 174, 135, 96, 57, 18`, totalling 1945
   unknown coefficients. The choice of `D` is what makes the later divisibility argument work:
   `deg_x Q(x, f(x)) <= max_b (369 - 39b + 39b) = 369 < 2*185 = 370`.

2. **Impose double vanishing at all 512 points.** For every received pair `(x_j, y_j)` require
   `Q(x_j, y_j) = 0`, `(dQ/dx)(x_j, y_j) = 0` and `(dQ/dy)(x_j, y_j) = 0`. That is
   `3*512 = 1536` homogeneous linear equations over GF(2^31-1). We do not know which points are
   honest, so the conditions are imposed everywhere; the honest ones are what the degree bound then
   exploits.

   At an honest point `Q(x, f(x))` and its derivative both vanish, so each of the 185 honest
   `x`-values is a double root of the univariate polynomial `Q(x, f(x))`, which has at most 369
   roots available. Hence `Q(x, f(x)) = 0` identically, i.e. **every nonzero solution of the system
   is divisible by the factor `(y - f(x))`**. The corrupted points contribute no information and no
   obstruction.

3. **Solve the system and pick a random `Q`.** Modular Gaussian elimination on the
   1536 x 1945 matrix over GF(2^31-1) measured `rank = 1536`, `nullity = 409`. Random values on the
   free columns and back-substitution give one concrete `Q`. Any nonzero element of that space is
   usable; the script draws a fresh one per attempt if a later step fails.

4. **Find the `(y - f)` factor without bivariate factorisation.** Pick a random `x0` in the field
   with the leading `y`-coefficient `Q_9(x0) != 0`, then factor the univariate polynomial
   `Q(x0, y)` of degree 9 over GF(2^31-1) and keep its roots `z` that lie in the base field
   (`sympy.factor_list` over `GF(p)`). For each such `z` with
   `(dQ/dy)(x0, z) != 0`, lift the branch `y = F(t)`, `t = x - x0`, as a formal power series
   satisfying `Q(x0 + t, F(t)) = 0` order by order (Hensel lifting: the coefficient of `t^s` is
   linear in the unknown `F_s` with invertible multiplier `(dQ/dy)(x0, z)`).

   The true `f` is a polynomial, so its branch has no pole: it is exactly the branch that
   **truncates**, i.e. whose series coefficients vanish from index `K = 40` onward. Testing
   `F_40 .. F_47 == 0` filters the genuine root out of the other branches, whose expansions do not
   terminate. Re-expanding the 40 surviving coefficients in the `x` basis yields `f`.

5. **Verify, then unwrap the flag.** Evaluating the candidate at all 512 `x` values gives
   **exactly 185 agreements**, matching the declared `t`. The 40 coefficients, joined low-order
   first as decimal strings and SHA-256 hashed, give the AES-GCM key; `decrypt_and_verify` accepts
   the tag, so the plaintext below is authenticated rather than a guess.

```text
[gs] unknowns=1945 equations=1536 deg_y=9 D=369 (need agreements >= 185)
[gs] rank=1536 nullity=409
[gs] attempt 0: found f with 185 agreements
[main] coeffs (low->high): [68199953, 428596489, 1836628629, 1104814632, 1273143446, 572910986, 305777953, 1449499247, 93560702, 550055166, 521878022, 2036679308, 1246796936, 1677818762, 1078223753, 115546409, 1807069105, 1312518364, 94380390, 587330116, 524413091, 440882059, 1062200812, 459052732, 847902277, 186832193, 1312408255, 1258337141, 1010443389, 1288558778, 1093591191, 917136146, 1685571284, 817082845, 38737022, 2087760572, 725603002, 785288899, 1179372709, 1662587097]
[main] flag: isfcr{l1st_d3c0d1ng_p4st_th3_r4d1us}
```

## Flag

`isfcr{l1st_d3c0d1ng_p4st_th3_r4d1us}`

Recovered by Guruswami-Sudan list decoding of the supplied `output.json`. Verification scope: the
decoded polynomial reproduces the promised agreement count (185 of 512) and the flag decrypts under
the AES-GCM tag sealed with its coefficients, which authenticates the coefficient vector itself.
No submission response was recorded, so acceptance by the CTF service is unconfirmed.

## Reproduce

Prerequisites: Python 3.12 with `numpy`, `sympy` and `pycryptodome`. Put `gs.py` next to the given
`output.json`. First check the decoder against a self-generated instance of the same shape
(smaller: `k=5, n=40, t=16`), which must print `[selftest] OK`:

```bash
python gs.py --test
python gs.py output.json
```

Expected tail of the second command (elapsed time varies with load; a SymPy deprecation warning
about modular integer comparison is unrelated noise):

```text
[gs] rank=1536 nullity=409
[gs] attempt 0: found f with 185 agreements
[main] elapsed 31.0s
[main] flag: isfcr{l1st_d3c0d1ng_p4st_th3_r4d1us}
```

Final script used for the solve:

```python
#!/usr/bin/env python3
"""Guruswami-Sudan list decoding (multiplicity m=2) for the 'half-truths' shares.

Interpolation: Q(x,y) = sum_b y^b Q_b(x), deg Q_b <= D - (k-1)b with D = m*tau - 1,
so deg_x Q(x,f(x)) <= D < m*tau; double vanishing at all n points then forces
(y - f) | Q for the true degree-(k-1) polynomial f with tau agreements.
Root finding: lift the F_p-roots of Q(x0,y) as power series in t = x - x0 and keep
the branches that truncate at degree < k.
"""
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np


# ---------------- univariate polynomials over GF(p), low -> high ----------------
def trim(a):
    a = list(a)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def deg(a):
    return len(trim(a)) - 1


def linear_roots(f, p, rng):
    """All roots in GF(p) of f, via sympy's finite-field factorisation."""
    from sympy import GF, Poly, Symbol, factor_list

    y = Symbol("y")
    f = trim(f)
    if deg(f) == 0:
        return []
    L = Poly(sum(int(c) * y ** i for i, c in enumerate(f)), y, domain=GF(p))
    roots = []
    for fac, _ in factor_list(L)[1]:
        if fac.degree() == 1:
            ac, bc = [int(v) for v in fac.all_coeffs()]
            roots.append((-bc * pow(ac, p - 2, p)) % p)
    return roots


# ---------------- series / shift helpers ----------------
def shift_series(coeffs, x0, M, p):
    """Series mod t^M of poly(x0 + t)."""
    out = [0] * M
    term = [1] + [0] * (M - 1)  # (x0+t)^a, start a=0
    for a, c in enumerate(coeffs):
        if c:
            for s in range(M):
                out[s] = (out[s] + c * term[s]) % p
        nxt = [0] * M
        for s in range(M):
            v = x0 * term[s] % p
            if s:
                v = (v + term[s - 1]) % p
            nxt[s] = v
        term = nxt
    return out


def to_x_basis(series, k, x0, p):
    """sum_s series[s]*(x-x0)^s -> coefficients in x."""
    out = [0] * max(k, len(series))
    term = [1] + [0] * (k - 1)
    for s in range(k):
        c = series[s]
        if c:
            for a in range(len(term)):
                out[a] = (out[a] + c * term[a]) % p
        nxt = [0] * k
        for a in range(len(term)):
            v = (-x0) * term[a] % p
            if a:
                v = (v + term[a - 1]) % p
            nxt[a] = v
        term = nxt
    return trim(out)


def henkel_lift(S, z, M, p):
    """Branch of Q(x0+t, y)=0 with y(0)=z, as series in t."""
    B = len(S) - 1
    zp = [1]
    for _ in range(B):
        zp.append(zp[-1] * z % p)
    G0 = sum(b * zp[b - 1] * S[b][0] for b in range(1, B + 1)) % p
    if G0 == 0:
        return None
    inv_G0 = pow(G0, p - 2, p)
    F = [0] * M
    F[0] = z
    for s in range(1, M):
        # powers of F mod t^M
        pows = [[1] + [0] * (M - 1)]
        for b in range(1, B + 1):
            nxt = [0] * M
            prev = pows[-1]
            for i in range(M):
                if prev[i]:
                    for j in range(M - i):
                        nxt[i + j] = (nxt[i + j] + prev[i] * F[j]) % p
            pows.append(nxt)
        w = 0
        for b in range(B + 1):
            Sb, Pb = S[b], pows[b]
            for i in range(s + 1):
                if Sb[i] and Pb[s - i]:
                    w = (w + Sb[i] * Pb[s - i]) % p
        F[s] = (-w) * inv_G0 % p
    return F


# ---------------- GS interpolation ----------------
def build_system(shares, p, k, tau, m):
    D = m * tau - 1
    km1 = k - 1
    B = D // km1
    db = [D - km1 * b for b in range(B + 1)]
    idx_b, idx_a = [], []
    for b in range(B + 1):
        for a in range(db[b] + 1):
            idx_b.append(b)
            idx_a.append(a)
    idx_b = np.array(idx_b, dtype=np.int64)
    idx_a = np.array(idx_a, dtype=np.int64)
    nU = len(idx_b)
    xs = np.array([s[0] for s in shares], dtype=np.int64)
    ys = np.array([s[1] for s in shares], dtype=np.int64)
    # power tables
    Xp = np.ones((len(shares), D + 1), dtype=np.int64)
    for a in range(1, D + 1):
        Xp[:, a] = Xp[:, a - 1] * xs % p
    Xp1 = np.ones((len(shares), D), dtype=np.int64)  # x^(a-1)
    for a in range(1, D):
        Xp1[:, a] = Xp1[:, a - 1] * xs % p
    Yp = np.ones((len(shares), B + 1), dtype=np.int64)
    for b in range(1, B + 1):
        Yp[:, b] = Yp[:, b - 1] * ys % p
    rows = np.empty((3 * len(shares), nU), dtype=np.int64)
    yb = Yp[:, idx_b]
    xa = Xp[:, idx_a]
    rows[0::3] = yb * xa % p
    dyb = np.where(idx_b[None, :] == 0, 0, idx_b[None, :] * Yp[:, np.maximum(idx_b - 1, 0)] % p)
    rows[2::3] = dyb * xa % p
    dxa = np.where(idx_a[None, :] == 0, 0, idx_a[None, :] * Xp1[:, np.maximum(idx_a - 1, 0)] % p)
    rows[1::3] = yb * dxa % p
    return rows, idx_b, idx_a, db, B, D


def eliminate(A, p):
    m_, n_ = A.shape
    pivots = []
    r = 0
    t0 = time.time()
    for c in range(n_):
        if r >= m_:
            break
        nz = np.flatnonzero(A[r:, c])
        if nz.size == 0:
            continue
        i = r + int(nz[0])
        if i != r:
            A[[r, i]] = A[[i, r]]
        pv = int(A[r, c])
        if pv != 1:
            A[r, c:] = A[r, c:] * pow(pv, p - 2, p) % p
        if r + 1 < m_:
            fac = A[r + 1:, c]
            sel = np.flatnonzero(fac)
            if sel.size:
                prow = A[r, c:]
                blk = 256
                for s0 in range(0, sel.size, blk):
                    rr = r + 1 + sel[s0:s0 + blk]
                    sub = (fac[sel[s0:s0 + blk]][:, None] * prow[None, :]) % p
                    A[rr, c:] = (A[rr][:, c:] - sub) % p
                    A[rr, c] = 0
        pivots.append(c)
        r += 1
        if r % 200 == 0:
            print(f"    [elim] pivot {r} / {m_}  ({time.time()-t0:.1f}s)", flush=True)
    return pivots, r


def random_nullspace(A, pivots, nU, rng):
    pivset = set(pivots)
    free = [c for c in range(nU) if c not in pivset]
    x = np.zeros(nU, dtype=np.int64)
    for c in free:
        x[c] = rng.randrange(1, 1 << 30)
    for ri in range(len(pivots) - 1, -1, -1):
        pc = pivots[ri]
        prod = np.mod(A[ri, pc + 1:] * x[pc + 1:], A_p)
        s = int(prod.sum(dtype=np.int64) % A_p)
        x[pc] = (-s) % A_p
    return x


A_p = None  # field modulus, set globally for random_nullspace


# ---------------- driver ----------------
def agree_count(coeffs, p, xs, ys, k):
    acc = np.zeros(len(xs), dtype=np.int64)
    for c in reversed(coeffs):
        acc = (acc * xs + c) % p
    return int(np.count_nonzero(acc == ys))


def run(shares, p, k, tau, n, m=2, tries=12, M_extra=8, seed=0xC0FFEE):
    rng = random.Random(seed)
    global A_p
    A_p = p
    rows, idx_b, idx_a, db, B, D = build_system(shares, p, k, tau, m)
    nU = rows.shape[1]
    print(f"[gs] unknowns={nU} equations={rows.shape[0]} deg_y={B} D={D} "
          f"(need agreements >= {tau})", flush=True)
    pivots, rank = eliminate(rows, p)
    nullity = nU - rank
    print(f"[gs] rank={rank} nullity={nullity}", flush=True)
    xs = np.array([s[0] for s in shares], dtype=np.int64)
    ys = np.array([s[1] for s in shares], dtype=np.int64)
    M = k + M_extra
    for attempt in range(tries):
        x = random_nullspace(rows, pivots, nU, rng)
        Qb = [[] for _ in range(B + 1)]
        for c, (b, a) in enumerate(zip(idx_b.tolist(), idx_a.tolist())):
            Qb[b].append((a, int(x[c])))
        Qb = [[v for _, v in sorted(lst)] for lst in Qb]
        for b in range(B + 1):  # pad
            Qb[b] += [0] * (db[b] + 1 - len(Qb[b]))
        for _ in range(6):
            x0 = rng.randrange(1, p)
            lead = sum(co * pow(x0, a, p) for a, co in enumerate(Qb[B])) % p
            if lead == 0:
                continue
            qy = [sum(co * pow(x0, a, p) for a, co in enumerate(Qb[b])) % p for b in range(B + 1)]
            f_y = trim(qy)
            if deg(f_y) == 0:
                continue
            try:
                roots = linear_roots(f_y, p, rng)
            except RuntimeError:
                continue
            S = [shift_series(Qb[b], x0, M, p) for b in range(B + 1)]
            for z in roots:
                F = henkel_lift(S, z, M, p)
                if F is None:
                    continue
                if any(F[s] for s in range(k, M)):
                    continue
                cand = to_x_basis(F, k, x0, p)
                cand = cand + [0] * (k - len(cand))
                t = agree_count(cand, p, xs, ys, k)
                if t >= tau:
                    print(f"[gs] attempt {attempt}: found f with {t} agreements", flush=True)
                    return cand, t
        print(f"[gs] attempt {attempt}: no truncating branch (Q not divisible by y-f?)", flush=True)
    return None, None


def finish(coeffs, out):
    key = hashlib.sha256((",".join(map(str, coeffs))).encode()).digest()
    from Crypto.Cipher import AES
    nonce = bytes.fromhex(out["flag_nonce"])
    ct = bytes.fromhex(out["flag_ct"])
    tag = bytes.fromhex(out["flag_tag"])
    pt = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ct, tag)
    return pt


def selftest():
    p = (1 << 31) - 1
    k, n, tau = 5, 40, 16
    rng = random.Random(7)
    coeffs = [rng.randrange(p) for _ in range(k)]

    def f(x):
        acc = 0
        for c in reversed(coeffs):
            acc = (acc * x + c) % p
        return acc

    xs = list(range(1, n + 1))
    honest = set(rng.sample(xs, tau))
    shares = []
    for x in xs:
        if x in honest:
            shares.append((x, f(x)))
        else:
            y = rng.randrange(p)
            while y == f(x):
                y = rng.randrange(p)
            shares.append((x, y))
    got, t = run(shares, p, k, tau, n, m=2, tries=4)
    print("[selftest] expected:", coeffs)
    print("[selftest] got     :", got, "agreements:", t)
    assert got == coeffs, "selftest FAILED"
    print("[selftest] OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        selftest()
        sys.exit(0)
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("output.json")
    out = json.loads(out_path.read_text())
    p, k, n, tau = out["p"], out["k"], out["n"], out["t"]
    shares = [(s[0], s[1]) for s in out["shares"]]
    assert len(shares) == n
    t0 = time.time()
    coeffs, agree = run(shares, p, k, tau, n, m=2)
    if coeffs is None:
        print("[main] FAILED to find f")
        sys.exit(1)
    print(f"[main] coeffs (low->high): {coeffs}")
    print(f"[main] elapsed {time.time()-t0:.1f}s")
    print("[main] flag:", finish(coeffs, out).decode(errors="replace"))
```
