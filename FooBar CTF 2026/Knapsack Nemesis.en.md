---
title: "Knapsack Nemesis"
category: "Crypto"
tags: ["knapsack", "merkle-hellman", "subset-sum", "meet-in-the-middle"]
solve_date: "2026-10-10T19:44:00+07:00"
language: "en"
points: 450
---

# Knapsack Nemesis

**Flag:** `foobarctf{l4tt1c3_r3duct10n_br34ks_m3rkl3_h3llm4n_9f4b!}`  
**Attachments:** `encrypt.py`, `output.txt`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `encrypt.py` | 1,868 | `6c9ea2034482ec03cb459e5199609f0a11278ef0332b2749cc9a197bb847f7eb` |
| `output.txt` | 1,161 | `7f0e953c597628652e54c288a09bf02b112b90de1ad9ff97795afaac423cd338` |

## Challenge

> A legacy archive still encrypts sensitive clearance tokens with the 1978 Merkle-Hellman knapsack cryptosystem. Management was assured that because the general Subset Sum problem is NP-complete, the cipher is unbreakable. Security was not consulted.
>
> We intercepted one public key vector and an encrypted transmission. Can you recover the secret flag?
>
> Hint: Is worst-case NP-completeness the same as average-case security? Check the knapsack density.

We are given the encryption source `encrypt.py` and output log `output.txt` containing a 32-element `PUBLIC_KEY` vector alongside 14 integer ciphertext blocks in `CIPHERTEXTS`.

## Analysis

The 1978 Merkle-Hellman knapsack system disguises a superincreasing knapsack sequence via modular multiplication:
$$b_i = w \cdot r_i \pmod q$$

Each 32-bit plaintext chunk $M = (m_0, m_1, \dots, m_{31}) \in \{0, 1\}^{32}$ is encrypted by computing the subset sum:
$$C = \sum_{i=0}^{31} m_i \cdot b_i$$

While general Subset Sum instances are NP-complete, the concrete security depends on the knapsack dimension $n$. Here, $n = 32$.

Because $n = 32$ is small, we do not even need low-density lattice reduction (Lagarias-Odlyzko / CLOS):
- A **Meet-in-the-Middle (MitM)** attack runs in $O(2^{n/2}) = O(2^{16})$:
  1. Split the public weights into two halves of 16 elements:
     $$B_{left} = B[:16], \quad B_{right} = B[16:]$$
  2. Precompute the $2^{16} = 65,536$ subset sums of the left half into a hash map:
     $$\text{map}[S_{left}] = \text{mask}_{left}$$
  3. For each target ciphertext block $C$, iterate through the $2^{16}$ possible right subset sums $S_{right}$ and query $C - S_{right}$ in the map.
  4. Upon finding a match, concatenate the two 16-bit masks to recover the original 32-bit (4-byte) block.

The left-half sum table is reused for all 14 ciphertext blocks; each block requires at most $2^{16}$ right-half lookups.

## Solution

1. Load `PUBLIC_KEY` and `CIPHERTEXTS` from `output.txt`.
2. Hash all $2^{16}$ subset sums for the first 16 public weights.
3. Decrypt each ciphertext block in `CIPHERTEXTS` via Meet-in-the-Middle.
4. Assemble the decrypted 4-byte chunks to reveal the flag.

## Result

```text
foobarctf{l4tt1c3_r3duct10n_br34ks_m3rkl3_h3llm4n_9f4b!}
```

## Reproduce

Execute the following standalone Python script:

```python
from pathlib import Path

# Load PUBLIC_KEY and CIPHERTEXTS
content = Path("output.txt").read_text()
scope = {}
exec(content, scope)
PUBLIC_KEY = scope["PUBLIC_KEY"]
CIPHERTEXTS = scope["CIPHERTEXTS"]

B_left = PUBLIC_KEY[:16]
B_right = PUBLIC_KEY[16:]

# 1. Precompute left subset sums
left_map = {}
for mask in range(1 << 16):
    s = 0
    val_left = 0
    for i in range(16):
        if (mask >> (15 - i)) & 1:
            s += B_left[i]
            val_left |= (1 << (15 - i))
    left_map[s] = val_left

# 2. Decrypt ciphertext blocks using MitM
flag_bytes = bytearray()
for c in CIPHERTEXTS:
    found = False
    for mask in range(1 << 16):
        s_right = 0
        val_right = 0
        for i in range(16):
            if (mask >> (15 - i)) & 1:
                s_right += B_right[i]
                val_right |= (1 << (15 - i))
        rem = c - s_right
        if rem in left_map:
            val = (left_map[rem] << 16) | val_right
            flag_bytes.extend(val.to_bytes(4, "big"))
            found = True
            break
    assert found, f"Solution not found for block {c}"

print(f"[+] Flag: {flag_bytes.decode()}")
```
