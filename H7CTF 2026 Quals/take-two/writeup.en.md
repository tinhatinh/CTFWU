# Take Two - Crypto (Hard)

**Flag:** `H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}`

## Challenge

Helios only boots firmware stamped by the notary. The notary refuses to sign any build containing `BACKDOOR`,
so there is no way to ask for a valid signature on the build we actually want. The line "it is not above a second take"
points at the break: a one-time signature leaf is allowed to sign again.

`lms.py` ships with the challenge, and it confesses itself: *"the vulnerability is operational (a leaf reused
via a counter reset), not in this code"*.

## Analysis

The scheme is WOTS+ sealed inside a Merkle tree of 16 leaves:

```python
msg_digits(msg):  d = sha256(msg) -> 64 nibble + 3 nibble checksum   # LEN = 67
wots_sign(sk,msg): sig[i] = chain(sk[i], d[i])                       # chain = hash tới trước
verify:  leaf = H(0x00 || H(chain(sig[i], 15-d_i))) compared to root via auth path
```

Two properties decide everything:

1. `chain` only goes one way. Knowing `chain(sk_i, a)` we can derive `chain(sk_i, a+k)` for any `k >= 0`,
   but we can never step back to `a-1`.
2. `verify` only checks that the signature matches the published root; there is no constraint saying the notary
   has to be the one who produced the signature.

The API gives exactly the three things needed: `POST /sign` (signs a message of our choice, provided it has no
`BACKDOOR`), `POST /rollback` (rewind counter), and `GET /root`.

A quick test: the first signature lands on leaf 1, after one rollback the leaf goes back to 0 and every later signing
reuses leaf 0. That is the "second take".

## Solution

**Step 1 - Gathering many signatures on the same leaf.** The `rollback -> sign("benign-<i>")` loop runs 260 times,
all of them on `leaf = 0`. For each coordinate `j` out of the 67 coordinates, record the smallest digit ever seen,
`mins[j]`, and the chain value `base[j] = sig[j]` at that digit.

**Step 2 - Check the coordinate minima.** For the 64 digest digits, an independent uniform-nibble model gives probability `1-(15/16)^k` of observing zero after `k` signatures. The three checksum digits do not follow that independent distribution. After 260 signatures, the observed `max(mins) = 1` and `sum(mins) = 1` mean 66 coordinates have minimum zero and one has minimum one. The next step checks the target against these measured minima.

**Step 3 - Signing the forbidden message.** For a target message whose digit is `t[j]`, all that is needed is
`t[j] >= mins[j]` to build:

```python
forged[j] = chain(base[j], t[j] - mins[j])
```

Since `mins` is almost entirely 0, this condition is almost always satisfied; in practice exactly 1 candidate
`HELIOS-OTA-BACKDOOR-1` had to be tried to cover every coordinate.

**Step 4 - Self-verification before submitting.** Using the challenge's own verify function, recompute the root from the
leaf implied by the forged signature and compare against the published root - it matches. This step is cheap and avoids
blindly guessing at a "deploy"; it also proves the signature is genuinely valid rather than the server being lenient.

**Step 5 - Deploy.**

```json
{"ok": true, "booted": true, "flag": "H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}"}
```

## Result
```bash
python exploit.py https://web-18955a87eb148fa7.web.h7tex.com
```

```
[*] leaf 0 signed 260 distinct messages (other leaves: [])
[*] per-coordinate min digit: max=1 sum=1
[+] target build found after 1 grind: HELIOS-OTA-BACKDOOR-1
[+] forged signature verifies against the published root locally
[*] deploy -> 200
[+] FLAG: H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}
```
