# Shared Blood — Crypto (Medium)

**Flag:** `H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}`
**Instance:** `https://web-bd09e5c5af420bbc.web.h7tex.com`

## Challenge

VoltEye cameras ship a whole fleet that is identical, "same production line, same amount of hurry". Among them is one
device whose console we want open. The challenge gives exactly three endpoints and no code at all.

## Initial Analysis

```
GET /          -> "Device fleet console. Admin bootstrap required."
                  GET /fleet · GET /captured · POST /admin {"token":"..."}
GET /fleet     -> {"e": 65537, "devices": [{"serial","n"} x30]}    modulus 1023/1024 bit
GET /captured  -> {"note": "RSA/PKCS1v1.5, encrypted to the device cert",
                   "serial": "VE-C1E90650", "e": 65537, "ciphertext": <128 byte hex>}
```

There is no decrypt oracle: only a single ciphertext, so the only path to the plaintext is factoring the target
device's modulus completely. A 1024 bit integer does not factor itself, but "family resemblance runs deeper than you'd
think" points straight at the classic fleet keygen bug: two devices drew the same prime.

## Exploit Chain

### Step 1: pairwise GCD over the whole fleet

```python
hits = [(a, b, math.gcd(an, bn))
        for i,(a,an) in enumerate(devs) for j,(b,bn) in enumerate(devs)
        if j > i and math.gcd(an, bn) > 1]
```

Out of C(30,2) = 435 pairs there is exactly one collision, and it involves the target directly:

```
[*] shared-prime pairs: 1
    VE-C1E90650 ~ VE-23795497   gcd = 512-bit prime
```

### Step 2: from one shared factor to the private key

```
p = 792448642746425956602219402032306819204...44085721   (512 bit)
q = n // p                                               (512 bit)
p * q == n  ->  True
phi = (p-1)*(q-1);  d = pow(65537, -1, phi);  m = pow(ct, d, n)
```

### Step 3: the PKCS#1 v1.5 vote

The decrypted block is 128 bytes long:

```
0002 81c2c61e...415d5d 00 766c745f343832353238633831343263613962316665353763666533
└type 2┘└── 97 byte padding, không có byte 0 ──┘└┘└──── message: "vlt_482528c8142ca9b1fe57cfe3" ────┘
```

The `00 02 PS 00 M` structure with a PS containing no zero byte confirms that the private key found is correct (a
single wrong bit in `d` would give garbage without the `00 02` prefix). The `vlt_<hex>` token also matches the form's
"admin bootstrap token" placeholder exactly.

### Step 4: submit

```
$ python solve_blood.py
[+] token = 'vlt_482528c8142ca9b1fe57cfe3'
[*] POST /admin -> 200 {"authed": true, "flag": "H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}"}
[+] FLAG: H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}
```

## Flag
```
H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}
```
