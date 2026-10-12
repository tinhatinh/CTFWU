---
title: "The Last Protocol"
category: "Crypto"
tags: ["rsa", "wiener-attack", "finite-state-machine", "feistel", "sha256", "jpeg-metadata", "stream-cipher"]
solve_date: "2026-10-10T20:25:00+07:00"
language: "en"
points: 983
---

# The Last Protocol

**Flag:** `kBxAc{cIPhEr_(h@in_ReCoNs7ru(tEd_31@90F84_FalS3_leAdS_De(iPheRed}`  
**Author:** HydraRoot  
**Attachment:** `thelastprotocol (1).zip` (100,632 bytes; SHA-256: `100d69e46e4d3da2f5ae35e1360e158dcf7ba5896e6285339e4a8bdb8be975ec`)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `archive.bin` | 24 | `ff962ec3a8270f4d7139f37e66aea62cc86bf85093dd1d073586741ebf9da704` |
| `archive.jpg` | 148,887 | `48cd800f6abb7bb5dc1bf6c3fa0b54f4362e696a9cac26f7ef2d924fc8eb488d` |
| `final.dat` | 370 | `04027aa227262f995e121631988f027a15acb81a0d6878df8a5d4415dbda56b7` |
| `fragment_01.dat` | 1,024 | `e85a42edaeb5a98664942ab3162d1c9cf78ccb168ed702ea45d68fd143eb1713` |
| `fragment_02.dat` | 1,036 | `1360c29b0081e99fa5712fda2a9133aafd92acc4860e34f3b0aa9821ae698664` |
| `fragment_03.dat` | 1,045 | `b8efc49320401afc283488bc64c83f4b9d6ba58428f1aea2a9b82ea5db932207` |
| `fragment_04.dat` | 1,024 | `773545fb16801d19b04eb0ec6892704281b8464d3f0530cf999feb7042a04192` |
| `notebook.pdf` | 3,777 | `31c87a59deffe0dfc02887cc44d6090c0313a3645daab8884e6478da5945ad99` |
| `transmission.dat` | 495 | `a0401ce918e638b5e3f7cd7df964dcbd25245b32b9b7de0065d4f93e3e53bad9` |


## Challenge

The intercepted message has three encryption stages. The RSA transmission contains unusual parameters. Once decrypted, it reveals the order of four calibration fragments. Each fragment contains measurements in mixed numeral systems and observations of a state machine. The recovered state history becomes Feistel key material. The decrypted archive then points to a JPEG comment needed to decrypt the final ciphertext. The challenge specifies the intended serialized history: `THE_LAST_PROTOCOL|state0:state1:...`.

## Analysis

### 1. Recovering the RSA plaintext with Wiener's attack

`transmission.dat` contains `n`, `e`, and `c`. The RSA private exponent is unusually small, making **Wiener's continued-fraction attack** on `e/n` effective. The recovered exponent and plaintext are:

```text
d = 109597755369341101
RSA plaintext = ORDER:03-01-04-02|NEXT:FRAGMENTS|CHECK:17
```

The fragments must be processed in the order **03→01→04→02**, not their filename order. `CHECK:17` is preserved as a marker from the message; the successful solution does not require reducing the measurements modulo 17.

### 2. Parsing mixed-base measurements and reconstructing the state history

Observation records follow this structure:

```text
<channel> | sample=<index> | fmt=<BIN|HEX|DEC> | value=<number>
```

The values must be converted from their declared base (`BIN`=2, `HEX`=16, `DEC`=10). Each fragment has two candidate channels in samples 00–07. Samples 08–09 contain only one measurement and are not part of the 32-state key material. The digits embedded in the six channel labels (`T9`, `K3`, `V8`, `R7`, `M2`, `Q4`) reveal a candidate cycle:

```text
9 -> 3 -> 8 -> 7 -> 2 -> 4 -> 9
```

At each of samples 00–07, select the measurement whose channel digit follows this state cycle. There are **two candidate paths per fragment**, giving **2^4 = 16** histories across four fragments. Exactly **one** candidate reproduces the ZIP notebook's Feistel test vector. Its path starting digits, in RSA fragment order, are `9, 2, 3, 4`.

The recovered 32 decimal states are:

```text
28476:44900:25841:59753:5171:4679:55113:51468:46083:31920:58185:21840:25453:39200:4872:56986:32349:57571:50713:11897:48565:18592:6165:12297:12273:53393:56625:49634:47558:55896:8129:10907
```

For example, fragment 03 follows `9,3,8,7,2,4,9,3` and contributes the values `28476,44900,25841,59753,5171,4679,55113,51468`.

### 3. Deriving the chained round keys and verifying Feistel

The notebook describes eight Feistel rounds over 64-bit blocks split into 32-bit big-endian halves, **without a final swap**. The SHA-256 material is derived as:

```python
serial = ':'.join(map(str, states)).encode('utf-8')
history = b'THE_LAST_PROTOCOL|' + serial
state_digest = SHA256(serial)
prev = SHA256(history)
for r in range(1, 9):
    prev = SHA256(prev + r.to_bytes(2, 'big') + state_digest)
    K_r = prev
```

Each round consumes only the **first eight bytes** of its 32-byte key, split into two 32-bit words. Its mixing function can be implemented as:

```python
MASK = 0xffffffff
k = int.from_bytes(K_r[:8], 'big')
x = (R ^ (k & MASK) ^ ((k >> 32) & MASK)) & MASK
x = (x + r * 0x9E3779B9) & MASK
sh = (3 * r) % 32
x = ((x << sh) | (x >> (32 - sh))) & MASK
x ^= (x >> 13) | ((x << 19) & MASK)
x = (x * 0x045D9F3B) & MASK
F = (x ^ (x >> 16)) & MASK
```

The forward Feistel round is `(L,R) <- (R, L XOR F(R,K_r,r))`; decryption traverses the rounds in reverse. The **actual test vector in the ZIP's `notebook.pdf`** is:

```text
Plaintext : 52 45 42 55 49 4C 44 3A  = "REBUILD:"
Ciphertext: BC BB AA 0C 38 91 AC B0
```

Those ciphertext bytes are also the first block of `archive.bin`. **Important notebook discrepancy:** another separately supplied PDF notebook specifies `FA D9 24 EE CF 4A DE AF` for the same plaintext. That vector does not match this archive; the bundled `BCBBAA0C3891ACB0` is the correct verification target here.

### 4. Decrypting `archive.bin`

`archive.bin` contains 24 bytes, or three eight-byte blocks. Reverse the eight Feistel rounds independently for each block to obtain:

```text
52454255494c443a54484548494444454e07070707070707
```

After removing the valid seven-byte PKCS#7 padding (`07` repeated seven times), the plaintext is:

```text
REBUILD:THEHIDDEN
```

`THEHIDDEN` is the recovered archive record, not the final flag.

### 5. Retrieving the JPEG recovery block

`archive.jpg` is already a complete JPEG inside the ZIP; the 24-byte Feistel archive does **not** decrypt into the full image. A JPEG comment contains:

```text
RECOVERED-BLOCK=d6d5da81f6bfffd0034b
VERIFY=49af4271c75288b0
```

The recovery value is **10 bytes** after hex decoding. Its integrity check hashes the **ASCII representation of the hex string**, not the decoded bytes:

```python
sha256(b'd6d5da81f6bfffd0034b').hexdigest()[:16]
# 49af4271c75288b0
```

### 6. Decrypting `final.dat`

The final file embeds a 65-byte hex ciphertext across multiple lines. Build a SHA-256 keystream using the reconstructed history and the recovered JPEG block:

```python
root = SHA256(history)  # including THE_LAST_PROTOCOL| prefix
block = bytes.fromhex('d6d5da81f6bfffd0034b')
stream_key = SHA256(root + block)
keystream = b''.join(
    SHA256(stream_key + i.to_bytes(4, 'big'))
    for i in range((len(ciphertext) + 31) // 32)
)
plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
```

This is a **SHA-256-derived XOR stream**, not AES-GCM. The entire 65-byte ciphertext decrypts into printable ASCII with the expected `kBxAc{...}` flag structure:

```text
kBxAc{cIPhEr_(h@in_ReCoNs7ru(tEd_31@90F84_FalS3_leAdS_De(iPheRed}
```

## Dead ends and pitfalls

| Attempt | Why it fails |
|---|---|
| Concatenate measurements in source order | The resulting keys do not pass the Feistel known-plaintext test. |
| Include samples 08–09 | They do not belong to the recovered 32-state history. |
| Treat `CHECK:17` as a mandatory modulus | The verified solution does not use it to reduce observations. |
| Verify against `FAD924EECF4ADEAF` | That is the conflicting, separately supplied notebook vector, not the ZIP archive's vector. |
| Guess an AES cipher for `final.dat` | The actual last stage is XOR with SHA-256-derived blocks. |

## Result

All stages have independent checks: RSA reveals the fragment order, the derived Feistel keys reproduce `REBUILD:`, the decrypted blocks have valid PKCS#7 padding, JPEG metadata passes SHA-256 verification, and the full final ciphertext decrypts into the flag.

```text
kBxAc{cIPhEr_(h@in_ReCoNs7ru(tEd_31@90F84_FalS3_leAdS_De(iPheRed}
```

## Reproduction

**Requirements:** Python 3.9+ and its standard library. Save the complete solver below as `solve_the_last_protocol.py` and provide the ZIP file as its argument.

```powershell
python solve_the_last_protocol.py "thelastprotocol (1).zip"
```

**Complete reproducible solver:**

```python
#!/usr/bin/env python3
"""Reproducible solver for HydraRoot's The Last Protocol (stdlib only).

Usage: python solve_the_last_protocol.py '/path/to/thelastprotocol (1).zip'
"""
import hashlib
import itertools
import math
import re
import sys
import zipfile
from collections import defaultdict

SHA = lambda data: hashlib.sha256(data).digest()
M32 = 0xFFFFFFFF
CYCLE = (9, 3, 8, 7, 2, 4)


def wiener_attack(n, e):
    # Continued-fraction convergents of e/n.
    num, den = e, n
    p0, p1, q0, q1 = 0, 1, 1, 0
    while den:
        a, num, den = num // den, den, num % den
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        k, d = p1, q1
        if k and (e * d - 1) % k == 0:
            phi = (e * d - 1) // k
            t = n - phi + 1
            discriminant = t * t - 4 * n
            if discriminant >= 0 and math.isqrt(discriminant) ** 2 == discriminant:
                return d
    raise ValueError('Wiener attack failed')


def read_observations(content):
    obs = defaultdict(dict)
    pattern = r'(\w+) \| sample=(\d+) \| fmt=(\w+) \| value=(\w+)'
    for channel, sample, fmt, val in re.findall(pattern, content.decode()):
        obs[int(sample)][channel] = int(val, {'BIN': 2, 'HEX': 16, 'DEC': 10}[fmt])
    return obs


def candidate_paths(obs):
    solutions = []
    for first in obs[0]:
        path = [int(first[1])]
        for s in range(1, 8):
            following = CYCLE[(CYCLE.index(path[-1]) + 1) % 6]
            if not any(int(ch[1]) == following for ch in obs[s]):
                break
            path.append(following)
        if len(path) == 8:
            solutions.append(path)
    return solutions


def f_round(v, key, r):
    k = int.from_bytes(key[:8], 'big')
    x = (v ^ (k & M32) ^ ((k >> 32) & M32)) & M32
    x = (x + r * 0x9E3779B9) & M32
    sh = (3 * r) % 32
    x = ((x << sh) | (x >> (32 - sh))) & M32
    x ^= (x >> 13) | ((x << 19) & M32)
    x = (x * 0x045D9F3B) & M32
    return (x ^ (x >> 16)) & M32


def feistel(block, keys, reverse=False):
    L = int.from_bytes(block[:4], 'big')
    R = int.from_bytes(block[4:], 'big')
    if not reverse:
        for r, key in enumerate(keys, 1):
            L, R = R, (L ^ f_round(R, key, r)) & M32
    else:
        for r in range(8, 0, -1):
            L, R = (R ^ f_round(L, keys[r - 1], r)) & M32, L
    return L.to_bytes(4, 'big') + R.to_bytes(4, 'big')


def derive_keys(states):
    serialized = ':'.join(map(str, states)).encode()
    full_history = b'THE_LAST_PROTOCOL|' + serialized
    digest = SHA(serialized)
    keys, prev = [], SHA(full_history)
    for r in range(1, 9):
        prev = SHA(prev + r.to_bytes(2, 'big') + digest)
        keys.append(prev)
    return keys, full_history


def main(path):
    with zipfile.ZipFile(path) as z:
        n, e, c = [int(re.search(rb'\b' + name + rb' = (\d+)',
                                 z.read('transmission.dat')).group(1))
                   for name in (b'n', b'e', b'c')]
        d = wiener_attack(n, e)
        rsa_plain = pow(c, d, n).to_bytes((n.bit_length() + 7) // 8, 'big').lstrip(b'\0')
        print('RSA:', rsa_plain.decode())
        assert b'CHECK:17' in rsa_plain
        names = re.search(rb'ORDER:([0-9-]+)\|NEXT:', rsa_plain).group(1).split(b'-')
        order = [int(x) for x in names]
        observations = {f: read_observations(z.read(f'fragment_{f:02}.dat')) for f in order}
        paths = [candidate_paths(observations[f]) for f in order]
        encrypted_archive = z.read('archive.bin')
        solution = None
        for choice in itertools.product(*paths):
            states = []
            for file_no, path_values in zip(order, choice):
                for sample, digit in enumerate(path_values):
                    states.append(next(v for channel, v in observations[file_no][sample].items()
                                       if int(channel[1]) == digit))
            keys, history = derive_keys(states)
            if feistel(b'REBUILD:', keys) == encrypted_archive[:8]:
                solution = states, keys, history
                break
        if solution is None:
            raise ValueError('Unable to verify recovered state history with Feistel vector')
        states, keys, full_history = solution
        print('States:', ':'.join(map(str, states)))
        decoded = b''.join(feistel(encrypted_archive[i:i+8], keys, reverse=True)
                           for i in range(0, len(encrypted_archive), 8))
        padding = decoded[-1]
        assert 1 <= padding <= 8 and decoded.endswith(bytes([padding]) * padding)
        archive_message = decoded[:-padding]
        print('Archive:', archive_message.decode())
        assert archive_message == b'REBUILD:THEHIDDEN'

        jpeg = z.read('archive.jpg')
        recovered_hex = re.search(rb'RECOVERED-BLOCK=([0-9a-f]+)', jpeg).group(1)
        verifier = re.search(rb'VERIFY=([0-9a-f]+)', jpeg).group(1)
        assert SHA(recovered_hex).hex()[:16].encode() == verifier
        recovered_block = bytes.fromhex(recovered_hex.decode())
        print('JPEG recovered block:', recovered_block.hex())

        final_note = z.read('final.dat').decode()
        part = final_note.split('The archive yielded this record:', 1)[1].split(
            "The operator's final note:", 1)[0]
        ciphertext = bytes.fromhex(''.join(re.findall(r'\b[0-9a-f]{10,}\b', part)))
        stream_key = SHA(SHA(full_history) + recovered_block)
        stream = b''.join(SHA(stream_key + i.to_bytes(4, 'big'))
                          for i in range((len(ciphertext) + 31) // 32))
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, stream))
        assert plaintext.startswith(b'kBxAc{') and plaintext.endswith(b'}')
        print('FLAG:', plaintext.decode('ascii'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'thelastprotocol.zip')
```

**Expected output:**

```text
RSA: ORDER:03-01-04-02|NEXT:FRAGMENTS|CHECK:17
States: 28476:44900:25841:59753:5171:4679:55113:51468:46083:31920:58185:21840:25453:39200:4872:56986:32349:57571:50713:11897:48565:18592:6165:12297:12273:53393:56625:49634:47558:55896:8129:10907
Archive: REBUILD:THEHIDDEN
JPEG recovered block: d6d5da81f6bfffd0034b
FLAG: kBxAc{cIPhEr_(h@in_ReCoNs7ru(tEd_31@90F84_FalS3_leAdS_De(iPheRed}
```
