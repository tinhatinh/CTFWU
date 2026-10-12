---
title: "linear_drift"
category: "Crypto"
tags: ["lfsr", "stream-cipher", "known-plaintext", "brute-force"]
solve_date: "2026-10-10T12:48:00+07:00"
language: "en"
points: 100
---

# linear_drift

**Flag:** `foobarctf{lfsr_st4t3_sp4c3_1s_w4y_t00_sm4ll_9b3c}`  
**Attachments:** `encrypt.py`, `challenge.txt`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `encrypt.py` | 1,485 | `3b77974c425c29c4accc93a1fb17e804e816f4a4c2ca270fb504b26627dabe8a` |
| `challenge.txt` | 134 | `d2efa316516d2ae0fc9261e169de8cf85861d2f702d3ca9c40e4fbaf4606bcd4` |

## Challenge

> Our hardware engineering team deployed a low-power IoT telemetry sensor in an industrial field station. To conserve CPU cycles and battery life on the node's 16-bit microcontroller, the lead engineer rolled out a custom hardware stream cipher based on a 16-bit Linear Feedback Shift Register (LFSR).
>
> Management was assured that because the 16-bit initial seed is generated randomly on every session, no unauthorized observer can decrypt the transmission.
>
> We intercepted a telemetry transmission containing the device's secret operational token. Can you recover the initial state and decrypt the flag?

We are given the cipher source code `encrypt.py` and the intercepted ciphertext in `challenge.txt`.

## Analysis

The cipher implements a 16-bit Galois/Fibonacci LFSR generator:
- State register width: 16 bits ($S \in [1, 2^{16} - 1]$).
- Feedback taps: `[16, 14, 13, 11]`.
- Keystream bytes are produced by taking 8 sequential output bits from the LFSR.
- Encryption operates via byte-wise XOR: $C = P \oplus K$.

The fundamental flaw lies in the key space:
- A 16-bit seed admits only $2^{16} - 1 = 65,535$ non-zero initial states.
- The standard flag format provides a known 10-byte plaintext prefix: `foobarctf{`.
- The first 10 keystream bytes are immediately determined by:
  $$K[:10] = P[:10] \oplus C[:10] = \text{b"foobarctf\{"} \oplus C[:10]$$

The solver tests all 65,535 candidate seeds against the known keystream prefix.

## Solution

1. Parse the hex-encoded ciphertext from `challenge.txt`.
2. Compute the target 10-byte keystream prefix from `foobarctf{`.
3. Iterate over all $seed \in [1, 65535]$, clocking the 16-bit LFSR to match the prefix.
4. With the matching seed (`60954` / `0xee1a`), generate the full keystream and decrypt the message.

## Result

Recovered seed:
- Decimal: `60954`
- Hex: `0xee1a`

```text
foobarctf{lfsr_st4t3_sp4c3_1s_w4y_t00_sm4ll_9b3c}
```

## Reproduce

Execute the following standalone Python script:

```python
from pathlib import Path

# Load ciphertext
chall_text = Path("challenge.txt").read_text()
ciphertext = bytes.fromhex(chall_text.split(":")[-1].strip())

prefix = b"foobarctf{"
expected_ks = bytes([p ^ c for p, c in zip(prefix, ciphertext[:len(prefix)])])

class LFSR:
    def __init__(self, state, taps):
        self.state = state & 0xFFFF
        self.taps = taps

    def step(self):
        feedback = 0
        for tap in self.taps:
            feedback ^= (self.state >> (tap - 1)) & 1
        out = self.state & 1
        self.state = ((self.state >> 1) | (feedback << 15)) & 0xFFFF
        return out

    def get_byte(self):
        b = 0
        for i in range(8):
            b |= (self.step() << i)
        return b

taps = [16, 14, 13, 11]

# Brute-force 16-bit seed
found_seed = None
for seed in range(1, 0x10000):
    lfsr = LFSR(seed, taps)
    ks = bytes([lfsr.get_byte() for _ in range(len(prefix))])
    if ks == expected_ks:
        found_seed = seed
        break

assert found_seed is not None, "Seed not found"
print(f"[*] Found seed: {found_seed} ({hex(found_seed)})")

lfsr = LFSR(found_seed, taps)
keystream = bytes([lfsr.get_byte() for _ in range(len(ciphertext))])
plaintext = bytes([c ^ k for c, k in zip(ciphertext, keystream)])
print(f"[+] Flag: {plaintext.decode()}")
```
