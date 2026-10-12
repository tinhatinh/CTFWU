---
title: "nebula_obscura"
category: "Crypto"
tags: ["aes-cbc", "prng-vigenere", "rsa", "pollard-p-minus-1", "multi-layer"]
solve_date: "2026-10-10T12:54:00+07:00"
language: "en"
points: 450
---

# nebula_obscura

**Flag:** `GLUG{T4K3_F1L3N4M3_53R10U5LY}`  
**Attachment:** `nebula_obscura_0xB4D455.enc`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `nebula_obscura_0xB4D455.enc` | 1,296 | `f7059d6c3615ded00adc4ccb8314749629397e546a882bbe8aec109a41658fa8` |

## Challenge

> You've intercepted a single encrypted file: nebula_obscura_0xB4D455.enc All we know:
>
> It was encrypted with AES-128-CBC. The key and IV are not provided separately — derive them from the file's own name. Whatever you decrypt will tell you how to proceed.

The challenge provides a single encrypted payload file `nebula_obscura_0xB4D455.enc`.

## Analysis

This challenge is a structured multi-layer puzzle chaining symmetric cipher derivation, PRNG stream construction, polyalphabetic substitution, and algebraic factoring.

### Layer 1 — AES-128-CBC from the filename

As hinted, the AES key and IV originate from the file's exact name string:
$$\text{digest} = \text{SHA-256}(\text{b"nebula\_obscura\_0xB4D455.enc"})$$
- Key (16 bytes): `digest[:16]`
- Initialization Vector IV (16 bytes): `digest[16:32]`

Decryption reveals a JSON object containing an embedded riddle:
> *"I am the exact number of seconds in half of an ordinary day. Take my value, hash it with SHA-256, and use the resulting hex digest as the seed string for Python's random module."*

Half an ordinary day is:
$$12 \text{ hours} = 12 \times 3,600 = 43,200 \text{ seconds}$$
The PRNG seed is the hexadecimal string `hashlib.sha256(b"43200").hexdigest()`, passed directly to `random.seed`.

### Layer 2 — PRNG keystream & Vigenère substitution

1. Seed the standard Python pseudo-random generator:
   $$\text{random.seed}(\text{SHA-256}(\text{"43200"}))$$
2. Generate a stream of random bytes and XOR it against `layer2_blob`.
3. The result is a custom Vigenère-encrypted ciphertext whose key is the first 10 hex characters of $\text{SHA-1}(\text{seed})$: `D9E8C73617`.
4. Decrypting the Vigenère layer yields a Base64 string that unmarshals into RSA parameters: modulus $n$, public exponent $e$, and ciphertext $c$.

### Layer 3 — RSA factoring via Pollard's $p-1$

The modulus $n$ is a 60-digit integer:
$$n = 165570081295982859187310065091722881855644781429813583648713$$

Testing for smooth group orders reveals that $p - 1$ has only small prime factors, making it vulnerable to **Pollard's $p-1$ algorithm**:
- $p = 1385691648282952313843858787803$
- $q = n / p = 1194855075677028975344337227411$

Computing Euler's totient $\phi(n) = (p - 1)(q - 1)$ and the private exponent $d \equiv e^{-1} \pmod{\phi(n)}$ yields $m = c^d \pmod n$, revealing the flag.

## Solution

1. Hash the filename using SHA-256 to decrypt the outermost AES-CBC layer.
2. Resolve the riddle to 43200, seed the Python PRNG, and perform the XOR and Vigenère decryptions.
3. Factor the composite RSA modulus $n$ using Pollard's $p-1$.
4. Reconstruct the private exponent $d$ and decrypt the ciphertext $c$.

## Result

```text
GLUG{T4K3_F1L3N4M3_53R10U5LY}
```

## Reproduce

Execute the following standalone Python script:

```python
import hashlib
import json
import base64
import random
from math import gcd
from Crypto.Cipher import AES
from pathlib import Path

# 1. Decrypt Layer 1 (AES-128-CBC)
filename = "nebula_obscura_0xB4D455.enc"
enc_data = Path(filename).read_bytes()

h = hashlib.sha256(filename.encode()).digest()
key, iv = h[:16], h[16:]
cipher = AES.new(key, AES.MODE_CBC, iv)
pt = cipher.decrypt(enc_data)
pad_len = pt[-1]
layer1_json = json.loads(pt[:-pad_len].decode())

# 2. Decrypt Layer 2 (PRNG & Vigenère)
# Half a day = 12 hours = 43200 seconds
seconds = "43200"
seed_str = hashlib.sha256(seconds.encode()).hexdigest()

random.seed(seed_str)
layer2_blob = bytes.fromhex(layer1_json["layer2_blob"])
ks = bytes([random.randint(0, 255) for _ in range(len(layer2_blob))])
vigenere_ct = bytes([c ^ k for c, k in zip(layer2_blob, ks)]).decode("latin-1")

vigenere_key = hashlib.sha1(seed_str.encode()).hexdigest()[:10].upper()

def vigenere_decrypt(ciphertext, key):
    res = []
    ki = 0
    for ch in ciphertext:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            k_shift = ord(key[ki % len(key)].upper()) - ord('A')
            res.append(chr((ord(ch) - base - k_shift) % 26 + base))
            ki += 1
        elif ch.isdigit():
            k_shift = int(key[ki % len(key)], 16) % 10
            res.append(chr((ord(ch) - ord('0') - k_shift) % 10 + ord('0')))
            ki += 1
        else:
            res.append(ch)
    return "".join(res)

b64_data = vigenere_decrypt(vigenere_ct, vigenere_key)
rsa_params = json.loads(base64.b64decode(b64_data).decode())

n = int(rsa_params["n"])
e = int(rsa_params["e"])
c = int(rsa_params["c"])

# 3. Factorize with Pollard's p - 1
a = 2
B = 1000000
for i in range(2, B):
    a = pow(a, i, n)
    d_cand = gcd(a - 1, n)
    if 1 < d_cand < n:
        p = d_cand
        break

q = n // p
phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)
m = pow(c, d, n)
flag = m.to_bytes((m.bit_length() + 7) // 8, "big").decode()
print(f"[+] Flag: {flag}")
```
