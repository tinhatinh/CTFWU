# Loose Lips - Crypto (Hard)

**Flag v1:** `H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}`
**Flag v2:** `H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}`
**Files:** `ckks.py` (2272 B, sha256 `f905e01981fc8049…`) · **Instance:** `https://web-550a48e366fd77e3.web.h7tex.com`

## Challenge

"DecryptoStat" processes statistics while (according to the ads) never seeing your data, using a shrunken CKKS
variant. Two services run in parallel: the original and a "hardened rewrite". Both have to be relieved of their secret
key; submit the key to `/v1/recover` or `/v2/recover` to receive the flag.

## Analysis

GET `/` returns a table describing the endpoints along with the cryptosystem parameters: `N=8`, `Q=2^40-87`,
`DELTA=2^25`, and the most important note: the secret key is a length-8 ternary vector.

In `ckks.py`:

```python
def small(bound=1): return [secrets.randbelow(2*bound+1) - bound for _ in range(N)]
def keygen(): return small(1)                    # each coefficient is only -1/0/+1
def encrypt(values, s):
    m = encode(values); a = rand_poly(); e = small(3)
    b = ring_add(ring_sub([0]*N, ring_mul(a, s)), ring_add(m, e))   # b = -a*s + m + e
    return b, a
def decrypt(ct, s, smudge=0):
    d = ring_add(b, ring_mul(a, s))              # b + a*s = m + e
    if smudge: d = ring_add(d, small(smudge))    # \"noise flooding\" of v2
    return decode(d)
```

Three facts combine into the solution:

3. `e = small(3)`, so every coefficient of `b + a*s - m` must lie in [-3, 3]. With modulus near `Q = 2^40`, this bound is used to filter the 6561 candidate keys.

The comment in `ckks.py` discusses a decryption oracle, and v2 adds `smudge` to decryption output. This solution instead enumerates the small keyspace and checks candidates against ciphertext from `/vN/encrypt`; it does not call the decryption oracle.

## Solution

### Step 1: request encryption of a zero plaintext

With `values = [0,0,0,0]` we get `m = encode(0) = 0`, so the only remaining condition is that `b + a*s = e` be small:

```python
c1 = post("/v1/encrypt", {"values": [0,0,0,0]})     # -> id, b, a
```

### Step 2: sweep the entire ternary keyspace, keep the keys that fit the noise budget

```python
m = ckks.encode(values)
for s in itertools.product((-1,0,1), repeat=8):
    d   = ckks.ring_add(c1["b"], ckks.ring_mul(c1["a"], list(s)))
    res = ckks.ring_sub(d, m)
    if max(abs(int(x.real)) for x in ckks._center(res)) <= 3:
        cand.append(list(s))
```

The challenge's `ckks.py` script is imported directly (`sys.path.insert(0,"files"); import ckks`) so that the
attacker's ring_mul/encode/_center match the server's 100%, avoiding any drift that could drop a valid solution.

Result: a single ciphertext already gave exactly one candidate for each of the two services, with no splitting round
needed:

```
=== v1 ===
[*] ternary keys matching the zero-plaintext ciphertext: 1 -> [[1, -1, 0, -1, 1, 1, -1, -1]]
=== v2 ===
[*] ternary keys matching the zero-plaintext ciphertext: 1 -> [[1, 0, 0, -1, -1, -1, 0, 1]]
```

### Step 3: prove it is the real key, then submit

Ask for a fresh ciphertext with `values=[1.5,-2.25,0.5,3.0]` and decrypt it yourself using the just-recovered key:

```
v1: local decrypt = [1.500000, -2.250000, 0.500000, 3.000000]  max|err| = 1.952e-07
    noise poly centred(b + a*s - m) = [ 2, -3, -3, 0, -3, 2,  1, -2]   (đúng budget small(3))
v2: max|err| = 1.836e-07
    noise poly centred(b + a*s - m) = [ 0,  3,  2,-2,  3,-2,  1, -2]
```

That means each service uses one fixed key across many requests, and that key correctly decrypts the ciphertexts it
generated itself.

`POST /v1/recover` and `POST /v2/recover`:

```
{"ok": true, "flag": "H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}"}
{"ok": true, "flag": "H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}"}
```

### Why the "hardened" build does not save v2

`smudge` affects the server’s decrypt result. The attack uses `(b, a)` from `/v2/encrypt` and checks keys locally, so that noise is outside the recovery path. The measured decrypt errors, 2.94e-07 in v2 and 1.95e-07 in v1, are additional observations of the oracle, not inputs to key recovery.

## Result
```
v1  H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}   key [1,-1,0,-1,1,1,-1,-1]
v2  H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}   key [1, 0, 0,-1,-1,-1, 0, 1]
```

Rerun: `python solve_lips.py` (recovers both, writes `flags.txt`).
