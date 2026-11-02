---
title: "Cipher"
category: "Mobile"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Cipher

## Challenge

The challenge is a locked Android vault APK. The vault data is encrypted with a key derived from a six-word passphrase. The app's `legacy` package contains an unused but fully implemented seed-based passphrase generator with only 2^18 possible seeds, so the passphrase can be brute-forced and the 64 vault records decrypted. Record 47 contains the flag.

## Solution

### Step 1: Reverse the crypto pipeline

From `classes*.dex`:

- `CryptoEngine`: passphrase -> PBKDF2-HMAC-SHA256 (32,768 iterations, 16-byte salt from `p7.bin`) -> root key. Each record derives an AES-256-GCM key with HKDF-SHA256 using the record salt and info `"v1" + index`; AAD is `"V1LT" + index`.
- `AnchorReader`: 16-byte verifier from `n3.bin` (96 bytes, XOR-decoded by position).
- `VaultStore`: `p7.bin` holds the `V1LT` magic, the salt and 64 records (index, nonce, ciphertext + tag).

### Step 2: Abuse the legacy seed window

The `legacy` package is not called by the UI, but it defines the intended weakness:

- `SeedWindow.base() = 0x2d8c0000`, `span() = 2^18` -> only 262,144 seeds.
- `LegacyPassphrase.fromSeed()` generates six words from `m4.bin` (XOR-masked lexicon) with `java.util.Random(0x6a09e667f3bcc909 ^ seed)` and a two-digit checksum.
- `Random.nextInt(100)` uses modulo plus rejection, not the high bits of `nextInt(256)`.

Brute-force the window and test each candidate against the HMAC verifier. The correct seed is:

```
seed       = 0x2d8ff383
passphrase = smxvoisk-fcxfgnpl-poznukfv-zxpmztpo-yanlxwmm-yanlxwmm-42
```

### Step 3: Decrypt the vault

Run the PBKDF2 -> HKDF -> AES-GCM pipeline over all 64 records. Record 47, titled "Archived security memo", contains:

```
hiCTF{cryptography_should_be_implemnetd_properly}
```



## Result

```
hiCTF{cryptography_should_be_implemnetd_properly}
```

## Reproduction notes

Preserve the spelling implemnetd in the flag. Full reproduction also requires the original APK and the complete m4.bin/n3.bin decoders and brute-force implementation, which are not included in this summary.
