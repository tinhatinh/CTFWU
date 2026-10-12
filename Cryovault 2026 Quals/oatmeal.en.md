---
title: "Oatmeal"
category: "Mobile"
tags: ["Reverse", "android", "vm"]
solve_date: "2026-10-11T09:25:00+07:00"
language: "en"
---

# Oatmeal

**Flag:** `isfcr{5958fbb07efd243b}`
**Artifacts:** `silvergate.apk` (12,921 bytes), `base.odex` (6,355 bytes)

| Artifact | SHA-256 |
|---|---|
| `silvergate.apk` | `704eaa66777b99a627f571a1be10446b61f40d855cbf3b48e69bb0ef4b568572` |
| `base.odex` | `3c10c7bcffee3f0487fad24c876d976cb07fcf739beb8b9d856628046a98b9c8` |

## Challenge

A device image of a person of interest was taken while it was running an in-house vault app called SilverGate. Two files came back from the image: the APK and an AOT-optimized artifact `base.odex`. The goal is to recover the vault's unlock material and the flag (`isfcr{...}`).

## Initial Analysis

Decompiling the APK with `jadx` yields a single activity, `com.silvergate.vault.LockActivity`:

- `checkFlag(pass)` returns true when `SHA256(pass)` equals a 32-byte constant `EXPECTED = 42b39944397bbbe271c695b40844f3f41c3a2b5a8d1c0400ce733878dbc44bb2`.
- `deriveFlag(pass)` outputs `isfcr{` followed by `hex(pass[i] ^ 'U')` per character.
- `assets/notes.txt` states: build target v1.3.2 (staging, confirmed by `versionName=1.3.2` in the binary AndroidManifest); the unlock passphrase lives in `secrets/vault_dev.yaml`, which is **not** present in the image; `EXPECTED` is the SHA-256 of the lowercased passphrase without trailing newline; and the "staging flag format" in `LockActivity.deriveFlag` is an open item to be replaced before v1.4 ships.

`base.odex` starts with the magic `oat\n243\0` and the string `ART-OPT/13.0.0-r43`, but it is not a real ELF-based OAT file. Its layout is bespoke, and disassembling the code regions with capstone (ARM64, matching the embedded `ARM64-A75` string) reveals three functions plus supporting data:

| Offset | Content |
|---|---|
| `0x180` / `0x198` / `0x1b0` | three 24-byte tables `A`, `B`, `C` |
| `0x1c8` | 32-byte SHA-256 constant, identical to the APK's `EXPECTED` |
| `0x1e8` | format string `isfcr{%016llx}` |
| `0x220`, `0x246` | two literal decoy flags (see below) |
| `0x290`..`0x4a2` | 530 bytes of custom bytecode (265 two-byte instructions) |
| `0x4b0` | `checkFlag_v1_LEGACY` - a bytecode-interpreting VM |
| `0x7e0` | `checkFlag_v2` - 32-byte `memcmp` against `0x1c8` |
| `0x820` | `finalizeFlag` - 24-byte FNV-1a-64 hash, then a final XOR |

Since the staging `vault_dev.yaml` is gone and SHA-256 is not invertible, the only path to the unlock secret is the legacy VM: it accepts or rejects a 24-byte input deterministically, so its expected input can be recovered byte by byte.

## Eliminated Hypotheses

- **The two literal flags in the ODEX.** `isfcr{dev_overlay_do_not_submit_18ca3b}` is self-labeled "do not submit", and neither string matches the staging format `isfcr{%016llx}` (their tails are 6 and 12 hex digits, not 16). They also cannot be outputs of `deriveFlag`, which only emits hex digits and never underscores. Decoys.
- **Feeding the recovered secret through the APK's `deriveFlag`.** That function is the post-staging replacement (per-char XOR-0x55 hex, 48 digits). The notes say the staging format was still in use in v1.3.2 and the replacement was an *open item for v1.4*; the ODEX - the compiled footprint of the staging build - embeds exactly the matching derivation: a 24-byte input, a 64-bit hash, and the `isfcr{%016llx}` format string. The VM also rejects this input under the APK's SHA check (`0cd23e48... != 42b3994...`), i.e. the SHA constant pins a *rotated* passphrase that is unrecoverable from the artifacts, while the ODEX preserves the working secret together with its flag function.
- **The trailing "dex" region (`0x890` to end).** The `dex\n035\0` magic is followed by a bogus checksum/`file_size`/endianness header, entropy is 7.96 bits/byte, and no zlib/bzip2/lzma stream starts there; XOR with the obvious keystreams (`0x55`, `0xa7`, `0x5c`, the passphrase) yields nothing. It is filler to match a real OAT footprint ("do not change the compiled footprint on A/B slots", per the notes).
- **Dictionary attack on the SHA constant.** Variants of the app/notes vocabulary (names, decoy tails, case and trailing-newline variants) produced no match for `42b3994...`.

## Exploitation Chain

1. **Reverse the VM semantics.** The interpreter at `0x4b0` requires a 24-byte input, then runs two-byte instructions `op|dst, arg` over 8 registers. Opcodes: 1 = load `input[arg]`, 2/3/4 = load `A/B/C[arg]` masked by `((arg + 0/24/48) * 0xa7) ^ 0x5c`, 5 = load immediate, 6 = add mod 256, 7 = xor, 8 = rotate-left by `arg & 7`, 9 = fail if registers unequal, 10 = accept. The bytecode is 24 blocks of 11 instructions plus the accept terminator; each block pins one input byte at a scrambled index, and its leading `r7 = imm; r6 = imm; r7 ^= r6` sequence is dead code.

2. **Invert each block.** Forward per byte `idx` with rotation `rot`:

   ```
   v = ROTL8( (input[idx] + (A[idx] ^ maskA(idx))) ^ (B[idx] ^ maskB(idx)) , rot)
   accept iff v == (C[idx] ^ maskC(idx))
   ```

   Solving backwards gives the unique byte for every index. Running over the real bytecode and tables yields the passphrase **`art_image_took_the_cake!`** (24 bytes). A forward simulation of the actual bytecode accepts it with the success opcode.

3. **Apply the staging flag derivation.** `finalizeFlag` computes FNV-1a 64-bit over the 24 bytes (`0xcbf29ce484222325`, prime `0x100000001b3`, 24 iterations), then XORs a constant assembled from `mov`/`movk` at `0x858`: `0xa55a96693c3cd2ad`. The result `0x5958fbb07efd243b` is formatted with the embedded staging string `isfcr{%016llx}`.

## Flag

`isfcr{5958fbb07efd243b}`

Recovered locally from the two artifacts. It was not submitted to the organizers' service during the solve, so acceptance is unconfirmed.

## Reproduce

Requires Python 3 and the two artifact files in the working directory. The `jadx`/capstone steps above are for inspection; the full recovery is self-contained:

```python
d = open("base.odex", "rb").read()
A, B, C = d[0x180:0x198], d[0x198:0x1b0], d[0x1b0:0x1c8]
bc = d[0x290:0x290 + 0x212]

def rol(v, n): n &= 7; return ((v << n) | (v >> (8 - n))) & 0xFF
def ror(v, n): n &= 7; return ((v >> n) | (v << (8 - n))) & 0xFF
mA = lambda i: ((i * 0xA7) ^ 0x5C) & 0xFF
mB = lambda i: (((i + 24) * 0xA7) ^ 0x5C) & 0xFF
mC = lambda i: (((i + 48) * 0xA7) ^ 0x5C) & 0xFF

# invert the 24 per-byte blocks
pw = [0] * 24
for k in range(24):
    b = bc[k * 22 : k * 22 + 22]
    idx, rot = b[7], b[17]
    v = ror((C[idx] ^ mC(idx)) & 0xFF, rot) ^ ((B[idx] ^ mB(idx)) & 0xFF)
    pw[idx] = (v - ((A[idx] ^ mA(idx)) & 0xFF)) & 0xFF
passphrase = bytes(pw)

# forward-simulate checkFlag_v1 over the real bytecode to confirm acceptance
R, ip, ok = [0] * 8, 0, False
while ip < len(bc):
    op, dst, arg = bc[ip] >> 4, bc[ip] & 0xF, bc[ip + 1]
    ip += 2
    if   op == 1:  R[dst] = passphrase[arg]
    elif op == 2:  R[dst] = (A[arg] ^ mA(arg)) & 0xFF
    elif op == 3:  R[dst] = (B[arg] ^ mB(arg)) & 0xFF
    elif op == 4:  R[dst] = (C[arg] ^ mC(arg)) & 0xFF
    elif op == 5:  R[dst] = arg
    elif op == 6:  R[dst] = (R[dst] + R[arg & 7]) & 0xFF
    elif op == 7:  R[dst] = (R[dst] ^ R[arg & 7]) & 0xFF
    elif op == 8:  R[dst] = rol(R[dst], arg & 7)
    elif op == 9:
        if R[dst] != R[arg & 7]:
            break
    elif op == 10:
        ok = True
        break

# finalizeFlag: FNV-1a-64 over 24 bytes, XOR post-mix constant
x = 0xCBF29CE484222325
for c in passphrase:
    x = (x ^ c) * 0x100000001B3 & (2**64 - 1)
x ^= 0xA55A96693C3CD2AD

print("passphrase :", passphrase.decode())
print("VM accepts :", ok)
print("FLAG isfcr{%016x}" % x)
```

Expected output:

```text
passphrase : art_image_took_the_cake!
VM accepts : True
FLAG isfcr{5958fbb07efd243b}
```
