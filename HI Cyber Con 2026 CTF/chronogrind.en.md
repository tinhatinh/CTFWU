---
title: "ChronoGrind"
category: "Crypto"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# ChronoGrind

## Challenge

A deliberately expensive crypto challenge. `state.dat` "keeps notes on itself", and the only key is the one you earn: the solver must grind through nine billion iterations to recover the 256-byte state value, derive `SHA-256(v)`, and decrypt a `CGFX` container protected with ChaCha20-Poly1305.

## Solution

### Step 1: Understand the container

The encrypted artifact uses a simple container:

```
"CGFX" | version (1 byte) | nonce (12 bytes) | Poly1305 tag (16 bytes) | ciphertext
```

The key is `SHA-256(v)`, where `v` is the 256-byte state value from `state.dat`. A synthetic round-trip (`CGFX` build -> ChaCha20-Poly1305 encrypt -> parse -> decrypt) was used to validate the format before the real grind.

### Step 2: Grind the state

The challenge is intentionally brute-force: the grind loop runs to `9,000,000,000` iterations at roughly 1.1M iterations/second. The state file is self-describing enough to keep the search honest; the recovered state yields the key.

### Step 3: Decrypt and verify

The decryption result printed:

```
it=9000000000 (100.000%) rate=1139690/s eta=0 s
DONE
SUCCESS v:sha256-be|tag-before-ct
b'hiCTF{n1c3_w0rk_n0w_t4k3_s0m3_r3$t}'
FLAG: hiCTF{n1c3_w0rk_n0w_t4k3_s0m3_r3$t}
EXIT=0
```

The recovered plaintext is the flag.

## Result

```
hiCTF{n1c3_w0rk_n0w_t4k3_s0m3_r3$t}
```

## Reproduction notes

Full reproduction requires the original state artifact and the transition-loop implementation. The container layout and final log do not define the grind algorithm by themselves.
