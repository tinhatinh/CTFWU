---
title: "Soul Ascension"
category: "Mobile"
tags: ["android", "native", "xtea", "fnv-1a", "androguard", "ghidra-headless"]
solve_date: "2026-10-09"
language: "en"
---

# Soul Ascension

**Flag:** `OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}`
**Artifact:** `SoulAscension.apk` (4978361 B) — `classes3.dex` (9052 B, the app) and `classes.dex` (7755924 B, AndroidX), plus `lib/arm64-v8a/libguardian.so` (417456 B, stripped, built with NDK r27, exporting `Java_com_byteme_soulascension_MainActivity_nativeFinal` at `0x27390`).

## Challenge

Soul Ascension (Mobile, Hard, 300 points, author Pratik Jadhav). The flag lives inside encrypted data in the native library, and the key can only be rebuilt after solving the four guardians in the Java layer.

## Analysis

The Java layer was read with androguard; `libguardian.so` was decompiled with Ghidra headless.

Java layer — four guardians, each contributing one fragment of the key chain:

- `memory`: length 6, condition `mix(w) == 44689`.
- `moon`: stored reversed (`noom`), giving `moon`.
- `soul`: `chr(c ^ 7) == "thrk"`.
- `2026`: `sum((d_i - 48) ^ (i + 3)) == 12`.

Concatenated into the chain:

```text
A9yromem:B4moon:C2tpvm:D82620
```

Native layer — `libguardian.so` uses XTEA with a key derived from that chain, then verifies the result with FNV-1a against the constant `0x757052CA`.

## Solution

Candidate chain variants are enumerated and each chaining model is tried; the model that passes the FNV-1a test decrypts the CBC blob into the flag:

```text
digit candidates: 326 ... [HIT] chain=A9yromem:B4moon:C2tpvm:D82620 cbc b'OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}'
raw plaintext: b'OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}\x01'
FLAG: OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian} len 39 FNV ok: True
```

The matching chain is `A9yromem:B4moon:C2tpvm:D82620`; the CBC plaintext is 39 bytes, exactly the flag length, with `FNV ok: True`. The trailing `\x01` byte is padding.

## Result

```text
OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}
```

The flag was reconstructed statically from the APK and matches the native FNV-1a check. A complete solver for the key derivation and XTEA-CBC stages is not included; the output shown is the saved result.

## Reproduce

Requires static analysis of `SoulAscension.apk`: androguard for the Java layer, Ghidra headless for `libguardian.so`. The solve decrypts the CBC block held in the native library using an XTEA key derived from the chain `A9yromem:B4moon:C2tpvm:D82620` and checks FNV-1a against `0x757052CA`; the APK is not run.
