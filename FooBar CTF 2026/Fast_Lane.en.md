---
title: "Fast_Lane"
category: "Crypto"
tags: ["rsa", "wieners-attack", "continued-fractions", "small-private-exponent"]
solve_date: "2026-10-10T12:50:00+07:00"
language: "en"
points: 300
---

# Fast_Lane

**Flag:** `foobarctf{w13n3r_c0nt1nu3d_fr4ct10ns_4r3_c00l}`  
**Attachment:** `encrypt.py`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `encrypt.py` | 1,672 | `97b5106253903d41eeb94f3fe7576dc8ca8c166545d69cb43523d2213494240b` |

## Challenge

> Our intern was told that RSA decryption is "too slow" on the company's embedded devices. His fix: pick a nice small private exponent so that decryption flies, then derive the public exponent from it.

The challenge provides a Python script `encrypt.py` declaring the RSA public parameters ($N, e$) alongside the ciphertext $c$.

## Analysis

In standard RSA, decryption runtime depends on the bit length of the secret exponent $d$ ($m = c^d \pmod N$). To speed up decryption on low-power hardware, the implementer selected a small private exponent $d$ (around 250 bits for a 1024-bit modulus $N$).

According to **Wiener's Theorem**:
- If $q < p < 2q$ and the private exponent $d$ satisfies:
  $$d < \frac{1}{3} N^{1/4}$$
- Then the fraction $\frac{k}{d}$ appears as one of the convergents in the continued fraction expansion of $\frac{e}{N}$.

By evaluating the continued fraction expansion of $\frac{e}{N}$, we generate candidate fractions $\frac{k_i}{d_i}$. For each convergent:
1. Estimate Euler's totient: $\phi(N) = \frac{e \cdot d_i - 1}{k_i}$.
2. Solve the quadratic equation for primes $p$ and $q$:
   $$x^2 - (N - \phi(N) + 1)x + N = 0$$
3. If the discriminant $\Delta = (N - \phi(N) + 1)^2 - 4N$ is a perfect square and the integer roots satisfy $p \cdot q = N$, then $d_i$ is the correct private exponent.

## Solution

1. Extract $N, e, c$ from `encrypt.py`.
2. Compute the continued fraction expansion of $\frac{e}{N}$ to iterate through convergents $\frac{k}{d}$.
3. Recover the valid private exponent:
   $$d = 1622505004839838179509349437221553670970557886884726952970445467324872749773$$
4. Compute $m = c^d \pmod N$ and decode the plaintext bytes.

## Result

```text
foobarctf{w13n3r_c0nt1nu3d_fr4ct10ns_4r3_c00l}
```

## Reproduce

Execute the following standalone Python script:

```python
import math

def continued_fraction(n, d):
    cf = []
    while d:
        q = n // d
        cf.append(q)
        n, d = d, n - q * d
    return cf

def convergents(cf):
    n0, n1 = 0, 1
    d0, d1 = 1, 0
    for q in cf:
        n2 = q * n1 + n0
        d2 = q * d1 + d0
        yield n2, d2
        n0, n1 = n1, n2
        d0, d1 = d1, d2

def wieners_attack(e, N):
    cf = continued_fraction(e, N)
    for k, d in convergents(cf):
        if k == 0:
            continue
        if (e * d - 1) % k != 0:
            continue
        phi = (e * d - 1) // k
        s = N - phi + 1
        discr = s * s - 4 * N
        if discr >= 0:
            t = math.isqrt(discr)
            if t * t == discr and (s + t) % 2 == 0:
                p = (s + t) // 2
                q = (s - t) // 2
                if p * q == N:
                    return d
    return None

N = 114011427936121493416621261814163322860096434550221402642990678015804218512747156680245710474660397120328699332762265784786531245150731102826913471259239450306988175648261976906874908844709990857810412071984457089341236975722221844465419237072540270093065558764264377516357792583574172428701930905572534318377
e = 52416943741266344043294019905127037839324497892798835456228974059083331984561105669144898909029422191945522212071781939986426635616794042824565210242641409721315572661916058055042146123874988338878664544220938885975304676235443124971951389785168227924875435889014226685752669326243730402760941085891202673157
c = 637576524592435297142718453021226879212940968795568072995087759676503491855498753207984050403167534081947932627650252256446013447972262017777446718860139252877882879968829102394227672092884370518311727317656037922833620592498820776072560622355085812111536039098800595299512191166479508205386700

d = wieners_attack(e, N)
assert d is not None, "Wiener's attack failed"
print(f"[*] Recovered d: {d}")

m = pow(c, d, N)
flag_bytes = m.to_bytes((m.bit_length() + 7) // 8, "big")
print(f"[+] Flag: {flag_bytes.decode()}")
```
