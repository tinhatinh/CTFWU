---
title: "Ghost in the Group"
category: "Crypto"
tags: ["diffie-hellman", "pohlig-hellman", "discrete-logarithm", "hkdf-sha256", "aes-256-gcm"]
solve_date: "2026-10-10T16:56:00+07:00"
language: "en"
points: 424
---

# Ghost in the Group

**Author:** HexAsh  
**Flag:** `kBxAc{tHe_ghO$T_!S_oN_Th3_W@Y_7o_THE_He1l_@nD_HEaVEN_CiTy_oF_gOD}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `ghostgroup.zip` | 1,061 | `11a9b06aa74dc2b5e43977f556ea917d59419a3ca84bb8654c88f7fdf08c1c87` |
| `report.txt` (inside ZIP) | 1,564 | `f5a595c067128d7bb52173b90eed777c0e37aa8d5a472487406db8c0086de84d` |

## Challenge

A gateway used finite-field Diffie–Hellman (DH) to derive an AES-GCM encryption key. We are given public parameters `p, g`, public keys `A, B`, HKDF salt/info, and an AES-GCM nonce/ciphertext, but no private exponent. We must recover the private exponent, compute the shared secret, and decrypt the message.

## Evidence

The recovered `report.txt` provides:

```text
p = 63467945649558061108050038689766719425570161602312573669177550438400000001
g = 34952038223805443010720493058853465706314868555565705932753928511299642526
A = 32042156517052529276780975726463240054802798908955726096181227009867410282
B = 37135947831804401007053458686511576709944818927810443240150867786090625989
KDF = HKDF-SHA256, salt=bb02b73977165f5eb5e4a68fe3a20d6f
info = ghost-in-the-group/aes-gcm, output=32 bytes
AEAD = AES-256-GCM, nonce=f5d4d68f2bbe8d324a1fea1a
```

DH security depends on the discrete logarithm `A = g^a mod p`. Although `p` is **246 bits**, a large modulus does not guarantee a hard group order.

## Weakness: smooth p−1

Factoring the multiplicative-group order:

```text
p - 1 = 2^24 · 3^12 · 5^8 · 7^6 · 11^4 · 13^3 · 17^3 · 19^2 · 23^2 · 29^2 · 31^2 · 37 · 41 · 43 · 47 · 53 · 59 · 61 · 67 · 162075354975923
```

We verified that `g` has full multiplicative order `p−1`. The order factors into many small prime powers; the largest remaining prime is `162075354975923` (48 bits). **Pohlig–Hellman** therefore reduces the original discrete logarithm to small subgroup logarithms plus one 48-bit subgroup problem (the most expensive step, solvable with Pollard rho/BSGS).

For each prime power `m = q^e`, compute:

```text
G_m = g^((p-1)/m) mod p
H_m = A^((p-1)/m) mod p
r_m = log_(G_m)(H_m) mod m
```

Combine all the congruences for `a` using the **Chinese Remainder Theorem (CRT)**.

## Recovering the private exponent

The recovered exponent is:

```text
a = 707872189507578477552274894304445771641188692329866348522823114155044802
```

Direct handshake verification succeeds:

```text
pow(g, a, p) == A   -> True
```

SageMath reproduction of the logarithm step (the 48-bit subgroup may require substantial computation):

```python
# Run with SageMath (Pohlig–Hellman + CRT).
p = ZZ(63467945649558061108050038689766719425570161602312573669177550438400000001)
g = ZZ(34952038223805443010720493058853465706314868555565705932753928511299642526)
A = ZZ(32042156517052529276780975726463240054802798908955726096181227009867410282)
order = p - 1
parts = factor(order)
residues, moduli = [], []
for ell, exponent in parts:
    m = ell ** exponent
    # Project into the subgroup of order m.
    base = Mod(power_mod(g, order // m, p), p)
    target = Mod(power_mod(A, order // m, p), p)
    # The largest prime factor (~48 bits) is the expensive step.
    r = discrete_log(target, base, ord=m, operation='*')
    residues.append(ZZ(r))
    moduli.append(ZZ(m))
a = CRT_list(residues, moduli)
assert power_mod(g, a, p) == A
print("a =", a)
print("shared =", power_mod(ZZ(37135947831804401007053458686511576709944818927810443240150867786090625989), a, p))
```

## Shared secret and decryption

Compute `S = B^a mod p`:

```text
7371495731907457570335172938636690069572639110804625667070088674540265086
```

For HKDF input, encode the **integer S as a minimal-length big-endian byte string (31 bytes)**. Do not use the ASCII decimal representation. HKDF-SHA256 with the supplied salt/info yields this 32-byte key:

```text
a9615ee5d4780da0830b6d5ece9d6baf2ab16996c0989922ee8e12fbca4c3125
```

The final **16 bytes of the ciphertext are the GCM authentication tag**. No AAD is supplied. Successful AESGCM decryption also verifies the tag.

## Independent verification (Python 3)

Install `cryptography` (`pip install cryptography`). This script uses the recovered exponent to verify the DH handshake and decrypt the original payload:

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

p = 63467945649558061108050038689766719425570161602312573669177550438400000001
g = 34952038223805443010720493058853465706314868555565705932753928511299642526
A = 32042156517052529276780975726463240054802798908955726096181227009867410282
B = 37135947831804401007053458686511576709944818927810443240150867786090625989
a = 707872189507578477552274894304445771641188692329866348522823114155044802  # recovered discrete log (also obtainable with the Sage code above)
assert pow(g, a, p) == A
S = pow(B, a, p)
assert S == 7371495731907457570335172938636690069572639110804625667070088674540265086

# The integer must be encoded as minimal-length big-endian bytes.
ikm = S.to_bytes((S.bit_length() + 7) // 8, 'big')
key = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=bytes.fromhex('bb02b73977165f5eb5e4a68fe3a20d6f'),
    info=b'ghost-in-the-group/aes-gcm',
).derive(ikm)
assert key.hex() == 'a9615ee5d4780da0830b6d5ece9d6baf2ab16996c0989922ee8e12fbca4c3125'
nonce = bytes.fromhex('f5d4d68f2bbe8d324a1fea1a')
ct_tag = bytes.fromhex(
    'b2fed82fa575a837bc583ee24799e5518d66c4e46a1fb981d4b20fa075b6fb15'
    'c1b84f3c1b6cf3d8d3cbe210b63b30df6264aed0ba08d8d93082736c9752c7714'
    'c4768676f68c9e3577aa6bd74f9562137'
)
flag = AESGCM(key).decrypt(nonce, ct_tag, None).decode('utf-8')
print('shared secret:', S)
print('AES-256 key:', key.hex())
print('flag:', flag)
```

Output:

```text
shared secret: 7371495731907457570335172938636690069572639110804625667070088674540265086
AES-256 key: a9615ee5d4780da0830b6d5ece9d6baf2ab16996c0989922ee8e12fbca4c3125
flag: kBxAc{tHe_ghO$T_!S_oN_Th3_W@Y_7o_THE_He1l_@nD_HEaVEN_CiTy_oF_gOD}
```

## Conclusion

The break comes from a **smooth group order**, not from simply guessing a 246-bit DH exponent. Pohlig–Hellman exposes the exponent; the derived DH shared secret produces the correct HKDF key; authenticated AES-GCM decryption reveals the flag.
