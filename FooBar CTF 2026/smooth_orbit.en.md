---
title: "smooth_orbit"
category: "Crypto"
tags: ["ecc", "ecdlp", "pohlig-hellman", "smooth-order", "crt"]
solve_date: "2026-10-10T12:55:00+07:00"
language: "en"
points: 500
---

# smooth_orbit

**Flag:** `foobarctf{p0hl1g_h3llm4n_sh4tt3rs_sm00th_curv3s_7a9c8e}`  
**Attachments:** `curve.py`, `challenge.txt`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `curve.py` | 2,057 | `374919361f0aa2221acda5d005efade4c1cf75f3379b047b94c11ee2844420b8` |
| `challenge.txt` | 940 | `808c5f8853ba1bf2482189f2a8cb06dfaf2b7ee68f824a2ea9e31ca04ddcbd62` |

## Challenge

> An aerospace defence contractor designed a secure satellite uplink system. Suspicious of standard NIST curves and Curve25519 due to fears of "hidden backdoors", their chief security architect generated a custom elliptic curve.
>
> We intercepted the public curve parameters, the base station's public key Q, and an encrypted emergency telecommand payload. Can you recover the master private key and decrypt the payload to retrieve the flag?

The attachment supplies the custom curve implementation `curve.py` along with the public parameters and encrypted telemetry in `challenge.txt`.

## Analysis

The system relies on a short Weierstrass elliptic curve:
$$y^2 \equiv x^3 + 3x \pmod p$$
defined over a 216-bit prime field $\mathbb{F}_p$, with base generator $G = (1, 2)$ and public key $Q = d \cdot G$.

The hardness of the Elliptic Curve Discrete Logarithm Problem (ECDLP) directly depends on the prime factorization of the group order $\text{ORDER}$. Factoring $\text{ORDER}$ reveals:

$$\text{ORDER} = 29 \times 41 \times 197 \times 257^2 \times 293 \times 421^2 \times 433 \times 449 \times 521 \times 593 \times 601 \times 617 \times 653 \times 661 \times 709 \times 829^2 \times 929 \times 941 \times 997^3$$

Every prime factor of $\text{ORDER}$ is bounded by $997$ ($\text{ORDER}$ is $997$-smooth).

Consequently, the **Pohlig-Hellman algorithm** reduces the ECDLP to small prime-power subgroups:
1. For each prime power $p_i^{e_i}$, project points into subgroup order $p_i^{e_i}$:
   $$Q_i = \left(\frac{N}{p_i^{e_i}}\right) Q, \quad G_i = \left(\frac{N}{p_i^{e_i}}\right) G$$
2. Since each prime factor $p_i \le 997$, solving the discrete log per subgroup via simple baby-step or exhaustive search is near-instantaneous.
3. Combine the congruences $d \equiv d_i \pmod{p_i^{e_i}}$ via the **Chinese Remainder Theorem (CRT)** to reconstruct the full private scalar $d$.
4. Derive the symmetric AES key as $\text{SHA-256}(\text{str}(d))$ and decrypt the AES-CBC payload.

## Solution

1. Factor $\text{ORDER}$ into its constituent prime powers.
2. Execute the Pohlig-Hellman procedure over elliptic curve points to compute each residue $d \pmod{p_i^{e_i}}$.
3. Reconstruct the private scalar via CRT:
   $$d = 1966488246008519752703905121425384383816541038606442439760348604$$
4. Decrypt the AES-CBC payload to recover the flag.

## Result

```text
foobarctf{p0hl1g_h3llm4n_sh4tt3rs_sm00th_curv3s_7a9c8e}
```

## Reproduce

Execute the following standalone Python script:

```python
import hashlib
from Crypto.Cipher import AES

p = 6521134753142873614843836235135002751093729570227995101024124417
a = 3
b = 0
G = (1, 2)
ORDER = 3260567376571436807421918117567548534157612337640795802440412833
Q = (2061573427100208603111671551304919028221649525354526770430156907, 6475257220252032604850487547502845101501630027536396815374309622)
Ciphertext = bytes.fromhex("a7d70d5eeb4e785225a542d003b29d1b1fe74c4cd270a5c42f940f108ebd9d27e5a910bd110e2cd5eba7eb6fd8ef3c64a5e46fe92717b7")

def point_add(P, Q):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0: return None
    if x1 == x2:
        m = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (m * m - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)

def scalar_mult(k, P):
    R = None
    T = P
    while k > 0:
        if k & 1:
            R = point_add(R, T)
        T = point_add(T, T)
        k >>= 1
    return R

def dlp_brute(P, Q, order):
    curr = None
    for d in range(order):
        if curr == Q:
            return d
        curr = point_add(curr, P)
    raise ValueError("DLP failed")

def pohlig_hellman_prime_power(P, Q, p_factor, e, N):
    gamma = scalar_mult(N // p_factor, P)
    x = 0
    for k in range(e):
        scalar = N // (p_factor ** (k + 1))
        Q_sub = point_add(Q, scalar_mult((-x) % N, P))
        H = scalar_mult(scalar, Q_sub)
        d_k = dlp_brute(gamma, H, p_factor)
        x += d_k * (p_factor ** k)
    return x

factors = [
    (29, 1), (41, 1), (197, 1), (257, 2), (293, 1), (421, 2), (433, 1),
    (449, 1), (521, 1), (593, 1), (601, 1), (617, 1), (653, 1), (661, 1),
    (709, 1), (829, 2), (929, 1), (941, 1), (997, 3)
]

congruences = []
for p_factor, e in factors:
    modulus = p_factor ** e
    rem = pohlig_hellman_prime_power(G, Q, p_factor, e, ORDER)
    congruences.append((rem, modulus))

def crt(congruences):
    M = 1
    for _, m in congruences: M *= m
    x = 0
    for a_i, m_i in congruences:
        M_i = M // m_i
        y_i = pow(M_i, -1, m_i)
        x = (x + a_i * M_i * y_i) % M
    return x

d = crt(congruences)
print(f"[*] Recovered scalar d: {d}")

key = hashlib.sha256(str(d).encode()).digest()
iv = Ciphertext[:16]
ct = Ciphertext[16:]
cipher = AES.new(key, AES.MODE_CBC, iv)
pt = cipher.decrypt(ct)
pad_len = pt[-1]
flag = pt[:-pad_len].decode()
print(f"[+] Flag: {flag}")
```
