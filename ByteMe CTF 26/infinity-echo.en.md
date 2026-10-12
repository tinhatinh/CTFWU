---
title: "Infinity Echo"
category: "Crypto"
tags: ["ecdsa", "nonce-reuse", "secp256k1", "xor-keystream"]
solve_date: "2026-10-09"
language: "en"
---

# Infinity Echo

**Flag:** `OWASP{th3_s0ul_st0n3_r3m3mb3rs_3v3ry_n0nc3}`
**Artifacts:** `curve.txt` (114 B), `signatures.txt` (487 B), `vault.bin` (43 B). Author: Pratik Jadhav.

## Challenge

Statement (Medium, 200 points):

```text
The Soul Stone signing system reused an ECDSA nonce. Recover the private key and use it to unlock the encrypted vault.
```

```text
curve=secp256k1
order=115792089237316195423570985008687907852837564279074904382605163141518161494337
hash=SHA-256
```

```text
z1=67347588885445611531902820368931932972040444711827578851545284568070995729591
r1=25051988655222711058432113143458427847319390342701470934547852446846422711567
s1=52962683639686838739783902028128198551006424233866284700402805681421689936337
z2=37899425276155539946685780241020155430073356926193948616690695112278990220884
r2=25051988655222711058432113143458427847319390342701470934547852446846422711567
s2=115743676190342659491968252099211722828859636197180484755175383932038123963381
```

`vault.bin` is 43 bytes with no identifiable header.

## Analysis

`r1 == r2`, while `z1 != z2` and `s1 != s2`. Assuming the same nonce `k` in `s = k^-1 (z + r*d) mod n` gives two equations in `k` and `d`. Matching `r` alone does not establish identical nonces:

```text
k = (z1 - z2) * (s1 - s2)^-1  mod n
d = (s1*k - z1) * r1^-1       mod n
```

The subtraction and the inverses are taken modulo `n`, the value on the `order=` line of `curve.txt`.

That constant is worth measuring carefully. The file gives `115792089237316195423570985008687907852837564279074904382605163141518161494337` = `0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141`, which is exactly the **group order** `n` of secp256k1. The field prime `p` of the same curve is `115792089237316195423570985008687907853269984665640564039457584007908834671663` = `0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f`. Both decimal values are 78 digits long, they agree in their first 38 digits and diverge only from digit 39 onward, which is precisely what makes this pair easy to mix up; two independent checks give the same verdict:

```text
order value == field prime P ? False
order value == group order N ? True
order * G is the point at infinity ? True
```

All of `z`, `r`, `s` are below `n`. `z1` and `z2` are supplied as integers, so the hashing step was already done by the challenge; the `hash=SHA-256` line takes no part in the recovery.

Running the recovery:

```text
r1 == r2 ? True
k = 123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234
d = 1a2b3c4d5e6f778899aabbccddeeff00112233445566778899aabbccddeeff11
sig1 residual (s*k - z - r*d) mod n = 0
sig2 residual (s*k - z - r*d) mod n = 0
```

Both values are recognisable patterned literals (`0x123456789abcdef` repeating, `0x1a2b3c4d5e6f...`), and both signature equations hold with residual exactly 0.

One point has to be recorded as an observation rather than an inference: the `r` given by the challenge is **not** `x(k*G) mod n`. Computing it independently on secp256k1 with the recovered `k`:

```text
x(k*G)      = 72588cf4bc7fb52a68d5c81b83643a96a881acfd9359d268bf675c0173b46920
r from file = 3762ec5011ac54e73768730a8b73619c69fa74f9bcf0263f37c9bf5733597d0f
x(k*G) mod n == r ? False
```

So this challenge does not follow the standard ECDSA relation on the `r` side; the solution travels along the algebraic system `s*k = z + r*d mod n` using `r` straight from the file, and is satisfied only in the residual sense. `d*G` yields a valid point `(0x908f37a8..., 0xc1b1bc2c...)`, but no artifact publishes a public key to compare against, so that point is not evidence.

For `vault.bin`, the key is derived from `d` and then applied as a repeating XOR by byte position:

```text
key = SHA256(b"SOUL-VAULT:" + str(d).encode())
```

The XOR key is `SHA256(b"SOUL-VAULT:" + str(d).encode())`, repeated over the ciphertext. The saved solver supplies the `SOUL-VAULT:` label, but the available record does not explain its discovery. Checking against the `OWASP{` crib gives:

```text
keystream[:6]: d7d8bb0bb267 | vault[:6]^OWASP{: d7d8bb0bb267
re-encrypt ok: True
plaintext: OWASP{th3_s0ul_st0n3_r3m3mb3rs_3v3ry_n0nc3}
```

The right-hand side of the first line does not use any decryption result: it only XORs the first 6 ciphertext bytes with `OWASP{`. The two sides match, and the 43 bytes of `vault.bin` equal the length of the recovered string, so the whole vault is the flag with no padding around it.

## Solution

Complete script, standard library only (`hashlib` plus hand-written curve arithmetic), reading all three artifacts:

```python
import hashlib

FIELD_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
GROUP_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def load(path):
    out = {}
    for line in open(path).read().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out

def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x1, y1 = A
    x2, y2 = B
    if x1 == x2 and (y1 + y2) % FIELD_P == 0:
        return None
    if A == B:
        lam = 3 * x1 * x1 * pow(2 * y1, -1, FIELD_P) % FIELD_P
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, FIELD_P) % FIELD_P
    x3 = (lam * lam - x1 - x2) % FIELD_P
    return (x3, (lam * (x1 - x3) - y1) % FIELD_P)

def mul(k, Pt):
    R, Q = None, Pt
    while k:
        if k & 1:
            R = add(R, Q)
        Q = add(Q, Q)
        k >>= 1
    return R

curve = load("curve.txt")
sig = load("signatures.txt")
n = int(curve["order"])
print("curve.txt:", curve)
print("order value == field prime P ?", n == FIELD_P)
print("order value == group order N ?", n == GROUP_N)
print("order * G is the point at infinity ?", mul(n, (GX, GY)) is None)

z1, r1, s1 = int(sig["z1"]), int(sig["r1"]), int(sig["s1"])
z2, r2, s2 = int(sig["z2"]), int(sig["r2"]), int(sig["s2"])
print("r1 == r2 ?", r1 == r2)

k = (z1 - z2) * pow(s1 - s2, -1, n) % n
d = (s1 * k - z1) * pow(r1, -1, n) % n
print("k = %064x" % k)
print("d = %064x" % d)
for i, (z, s) in enumerate(((z1, s1), (z2, s2)), 1):
    print("sig%d residual (s*k - z - r*d) mod n = %d" % (i, (s * k - z - r1 * d) % n))

R = mul(k, (GX, GY))
print("x(k*G)      = %064x" % R[0])
print("r from file = %064x" % r1)
print("x(k*G) mod n == r ?", R[0] % n == r1)
Q = mul(d, (GX, GY))
print("d*G = (%064x, %064x)" % (Q[0], Q[1]))

vault = open("vault.bin", "rb").read()
key = hashlib.sha256(("SOUL-VAULT:%d" % d).encode("ascii")).digest()
pt = bytes(a ^ key[i % 32] for i, a in enumerate(vault))
print("keystream[:6]:", key[:6].hex(), "| vault[:6]^OWASP{:",
      bytes(a ^ b for a, b in zip(vault[:6], b"OWASP{")).hex())
print("re-encrypt ok:", bytes(a ^ key[i % 32] for i, a in enumerate(pt)) == vault)
print("plaintext:", pt.decode())
```

```text
curve.txt: {'curve': 'secp256k1', 'order': '115792089237316195423570985008687907852837564279074904382605163141518161494337', 'hash': 'SHA-256'}
order value == field prime P ? False
order value == group order N ? True
order * G is the point at infinity ? True
r1 == r2 ? True
k = 123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234
d = 1a2b3c4d5e6f778899aabbccddeeff00112233445566778899aabbccddeeff11
sig1 residual (s*k - z - r*d) mod n = 0
sig2 residual (s*k - z - r*d) mod n = 0
x(k*G)      = 72588cf4bc7fb52a68d5c81b83643a96a881acfd9359d268bf675c0173b46920
r from file = 3762ec5011ac54e73768730a8b73619c69fa74f9bcf0263f37c9bf5733597d0f
x(k*G) mod n == r ? False
d*G = (908f37a80cad36ed8f161b25015574261675c74ccf1367e14c698a52c849fc53, c1b1bc2c5cbbdd8eb86da9a0e9603f58485f1ec2bba3d204575ec664daeab149)
keystream[:6]: d7d8bb0bb267 | vault[:6]^OWASP{: d7d8bb0bb267
re-encrypt ok: True
plaintext: OWASP{th3_s0ul_st0n3_r3m3mb3rs_3v3ry_n0nc3}
```

## Result

```text
OWASP{th3_s0ul_st0n3_r3m3mb3rs_3v3ry_n0nc3}
```

Decrypted locally from the artifact `vault.bin` with a key built from the recovered `d`; the keystream matches the `OWASP{` crib on the first 6 bytes and the reverse XOR reproduces the ciphertext exactly (`re-encrypt ok: True`). No remote service ships with this challenge. As noted in the Analysis, the `r` in the file is not `x(k*G) mod n`, so the solution does not replicate standard ECDSA in full. No submission response recorded.

## Reproduce

The main path needs Python 3 standard library only (`hashlib`). Save the block from the Solution section as `echo_all.py` in the same directory as `curve.txt`, `signatures.txt` and `vault.bin`:

```console
$ python echo_all.py
```

The recovery path above uses only the standard library; the unrelated key-search scripts are not needed.
