# Owner's Draw - Crypto (Medium)

**Flag:** `H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}`
**Instance:** `https://web-b39cfff63c4c78b9.web.h7tex.com`

## Challenge

OrionPay takes webhooks and only obeys paperwork when the paperwork "carries the right seal". One class of payout may
only be touched by the owner. We are given exactly one legitimate slip (its body plus its signature) and curiosity.

## Initial Analysis

```
GET /sample -> body        : event=payment.succeeded&amount=500&currency=usd&customer=cus_9f2a&role=guest
              X-Signature  : 14d500d5...d929f6a7
              signing      : SHA256(secret || body)
```

`POST /webhook` with the untouched slip returns `{"ok": true, "role": "guest", "note": "no owner payout"}` -> the
signature is verified before the body is parsed, and `role` is what decides the payout.

The weakness sits in the signing formula: `SHA256(secret || body)` is a prefix-style MAC over a Merkle - Damgård hash.
For this kind of construction the published digest is exactly SHA-256's internal state after processing the whole
padded message, so anyone holding (tag, original message length) can keep running the compression function over
appended data and produce a valid tag for `body || padding || extra`  -  without knowing `secret`.

`/v2/webhook` uses HMAC-SHA256: a direct measurement shows the same SHA-256 signature gets a 401, i.e. the "next-gen"
version closes exactly this hole (HMAC has inner and outer padding layers, so its state cannot be continued). The
challenge has a single objective, so v2 is there as the control.

## Exploit Chain

### Step 1: rebuilding SHA-256 compression in pure Python

`hashlib` has no "continue from a digest" API, so `compress(state, block)` has to be written by hand (message schedule +
64 rounds). This is where the challenge is harder than it looks: one wrong constant or one wrong state-update line
makes the entire forge void.

```python
def compress(h, block):
    w = list(struct.unpack(">16I", block))
    for i in range(16, 64):
        s0 = ror(w[i-15],7) ^ ror(w[i-15],18) ^ (w[i-15] >> 3)
        s1 = ror(w[i-2],17) ^ ror(w[i-2],19) ^ (w[i-2] >> 10)
        w.append((w[i-16] + s0 + w[i-7] + s1) & M)
    a, b, c, d, e, f, g, hh = h
    for i in range(64):
        S1 = ror(e,6) ^ ror(e,11) ^ ror(e,25); ch = (e & f) ^ (~e & g)
        t1 = (hh + S1 + ch + K[i] + w[i]) & M
        S0 = ror(a,2) ^ ror(a,13) ^ ror(a,22); mj = (a&b) ^ (a&c) ^ (b&c)
        t2 = (S0 + mj) & M
        hh, g, f, e, d, c, b, a = g, f, e, (d+t1)&M, c, b, a, (t1+t2)&M
    return tuple((x + y) & M for x, y in zip(h, (a,b,c,d,e,f,g,hh)))
```

### Step 2: splice

The original message the server signed is `secret || body`, of length `L = len(secret) + 76` (we do not know
`len(secret)`). The padding SHA-256 appended to the original message is `0x80 || 00*k || be64(8L)`, and that very part
is what we have to carry into the new body:

```python
pad  = b"\x80" + b"\x00" * ((55 - L) % 64) + struct.pack(">Q", L * 8)
new  = pad + b"&role=owner"
tag  = struct.unpack(">8I", bytes.fromhex(sig))      # = trạng thái sau pad
# run continuing from the tag above (new + its own padding)
```

### Step 3: probing the secret length, the server as an oracle

```python
for s_len in range(65):
    ext, forged = len_extend(tag, s_len + len(body), b"&role=owner")
    POST /webhook  body=body+ext  X-Signature=forged
```

401s in a row until `s_len = 15`:

```
[+] secret length guess=15   body tail=b'\x00\x00\x00\x02\xd8&role=owner'
[+] /webhook -> 200 {"ok": true, "payout": "authorized", "flag": "H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}"}
```

The 8 length bytes in the spliced padding are `0x2d8` = 728 bit = 91 byte = 15 (secret) + 76 (body)  -  a
self-verifying number: it points out the correct secret length without needing the server's response.

## Flag
```
$ python solve_draw.py
[+] FLAG: H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}
```
