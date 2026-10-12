---
title: "Vormir Common Modulus"
category: "Crypto"
tags: ["rsa", "common-modulus", "bezout"]
solve_date: "2026-10-09"
language: "en"
---

# Vormir Common Modulus

**Flag:** `OWASP{v0rm1r_tw1st3d_rsa_l34ks_th3_s0ul}`
**Artifact:** `params.txt` (386 B). Author: Pratik Jadhav.

## Challenge

Statement (Easy, 100 points):

```text
Two custodians encrypted the same Soul Vault secret using RSA with a shared modulus but different public exponents. Recover the plaintext.
```

The only input is `params.txt`, five `key = value` lines:

```text
n = 16380649768533394557837493376413306403300053927332145442950164332328030751564185489519565597585555867737606727528343
e1 = 65537
e2 = 65539
c1 = 13717084049277399427945358975177210874446528287993178469838547381506741616766449871863462627142297960244208456711847
c2 = 4601321998457411971134687661444766716276847022305030736758227088246554672740623255330037934526510403437754437399162
```

## Analysis

Measurements taken directly from the file rather than assumed:

```text
n bit_length     : 383
gcd(e1, e2)      : 1
m bit_length     : 319
```

`n` is 383 bits long. That is the length measured from `params.txt`, not a usual RSA width such as 1024 or 2048 bits.

The two pairs `(e1, c1)` and `(e2, c2)` share one `n`, and the statement says the plaintext is the same. The model is therefore:

```text
c1 = m^e1 mod n
c2 = m^e2 mod n
```

Because `gcd(e1, e2) = 1`, Bezout's identity gives `a`, `b` with `a*e1 + b*e2 = 1`, hence:

```text
c1^a * c2^b = m^(a*e1 + b*e2) = m  (mod n)
```

so the plaintext operator works without factoring `n`. Taking `a = pow(e1, -1, e2)` and `b = (1 - a*e1) // e2` yields `a = 32769`, `b = -32768`, and `32769*65537 - 32768*65539 = 2147581953 - 2147581952 = 1`.

A negative `b` means `c2^b` needs the modular inverse of `c2` modulo `n`; that inversion is the only step beyond exponentiation. `a` is already positive, so `c1` is used unchanged. After the sign fix the exponents actually applied are `a = 32769` and `b = 32768`, with `c2` replaced by `pow(c2, -1, n)`.

The recovered `m` is 319 bits, which fits the 40 ASCII bytes of the flag (40*8 = 320 bits, first byte below `0x80`), consistent with the unpadded textbook RSA the statement describes.

## Solution

The solve script (standard library only):

```python
from math import gcd
import ast, pathlib

src = pathlib.Path(__file__).with_name("params.txt").read_text()
ns = {}
for line in src.strip().splitlines():
    if line.strip():
        k, v = line.split("=")
        ns[k.strip()] = int(v)

n, e1, e2, c1, c2 = ns["n"], ns["e1"], ns["e2"], ns["c1"], ns["c2"]

assert gcd(e1, e2) == 1, "e1 and e2 not coprime"

# Bezout: a*e1 + b*e2 = 1
a = pow(e1, -1, e2)
b = (1 - a * e1) // e2

if a < 0:
    c1, a = pow(c1, -1, n), -a
if b < 0:
    c2, b = pow(c2, -1, n), -b

m = pow(c1, a, n) * pow(c2, b, n) % n
print("a,b =", (1 - a * e1) / e2, b)
print("m  =", m)

pt = m.to_bytes((m.bit_length() + 7) // 8, "big")
print("pt =", pt)
```

Output:

```text
a,b = -32768.0 32768
m  = 661996120338108837762769633508381563709412516386178580218881506680140567815232126603297643916413
pt = b'OWASP{v0rm1r_tw1st3d_rsa_l34ks_th3_s0ul}'
```

The `a,b` line prints two forms of the same coefficient: `-32768.0` is the Bezout `b` (float division), `32768` is the positive exponent used after `c2` was replaced by its inverse.

Verification that does not rely on the explanation: re-encrypt `m` under both exponents and compare against the ciphertexts in the file.

```python
from math import gcd
import pathlib

ns = {}
for line in pathlib.Path("params.txt").read_text().strip().splitlines():
    if line.strip():
        k, v = line.split("=")
        ns[k.strip()] = int(v)
n, e1, e2, c1, c2 = (ns["n"], ns["e1"], ns["e2"], ns["c1"], ns["c2"])

m = 661996120338108837762769633508381563709412516386178580218881506680140567815232126603297643916413
print("n bit_length     :", n.bit_length())
print("gcd(e1, e2)      :", gcd(e1, e2))
print("m bit_length     :", m.bit_length())
print("pow(m, e1, n) == c1 :", pow(m, e1, n) == c1)
print("pow(m, e2, n) == c2 :", pow(m, e2, n) == c2)
print("pt               :", m.to_bytes((m.bit_length() + 7) // 8, "big"))
```

```text
n bit_length     : 383
gcd(e1, e2)      : 1
m bit_length     : 319
pow(m, e1, n) == c1 : True
pow(m, e2, n) == c2 : True
pt               : b'OWASP{v0rm1r_tw1st3d_rsa_l34ks_th3_s0ul}'
```

## Result

```text
OWASP{v0rm1r_tw1st3d_rsa_l34ks_th3_s0ul}
```

Decrypted locally from the artifact `params.txt` and self-verified by re-encryption against both exponents; both ciphertext comparisons return `True`. This challenge ships no remote service. No submission response recorded.

## Reproduce

Python 3 only (`math`, `pathlib`); no cryptography library is needed. Put `solve.py` next to `params.txt`, since the script resolves that file relative to itself, then run:

```console
$ python solve.py
```

To run the verification independently, save the second block as `check_vormir.py` next to `params.txt` and run `python check_vormir.py`. That block hard-codes `m`, so it fails loudly if `params.txt` differs from the copy used above.
