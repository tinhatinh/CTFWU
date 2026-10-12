---
title: "SoulVault"
category: "Mobile"
tags: ["android", "jni", "radare2", "proof-of-work", "fnv-1a", "sha-256"]
solve_date: "2026-10-09"
language: "en"
---

# SoulVault

**Flag:** `OWASP{soul_vault_fragment_recovered}`
**Artifact:** `SoulVault.apk` (1454312 B) — contains only `classes2.dex`, `AndroidManifest.xml`, `res/layout/activity_main.xml` and `lib/{arm64-v8a,armeabi-v7a,x86,x86_64}/libsoulgate.so`.

## Challenge

SoulVault (Mobile, Medium, 200 points, author Pratik Jadhav): "Analyze the Android client and native proof-of-work flow to unlock the Soul Vault." The client talks to the backend `https://byteme-soulvault-api.onrender.com`. A separate challenge with the same name, "SoulVault", exists under Reverse Engineering (slug `soulvault-go`) and is unrelated to this one.

## Analysis

The Java layer was decompiled with the jadx CLI (`jadx.cli.JadxCLI`; the PATH launcher opens the GUI, so it is unusable for batch work). This yields the two native methods `SoulBridge.p` and `SoulBridge.q`, the device string `MANUFACTURER:MODEL:SDK_INT`, and the base URL above.

The native `libsoulgate.so`, analysed with radare2, exposes three pieces:

- A 22-byte blob at `.rodata:0x14d20` which, XORed with the repeating key `"Soul-Gate-917"`, gives the endpoint path `/v1/soul/echo/fragment`.
- `p@0x26010` computes FNV-1a (offset basis `0x811c9dc5`, prime `0x1000193`), then `h ^= h >> 13`, `rotl(h, 7)`, `h ^ len*0x9e3779b9`, followed by a murmur finalizer; the result is formatted as `g3-%08x`. This is the client token.
- `q@0x26420 → 0x266c0` is a 4-round SHA-256 chain whose acceptance test is `difficulty` leading zero bits. This is the proof-of-work loop.

## Solution

The unlock flow: `GET` the endpoint to obtain `difficulty`, `nonce`, `ticket`; build the client token `g3-…` with `p`; then run `q` over a seed whose first component is the client token, incrementing a counter until the SHA-256 digest has the `difficulty` leading zero bits, and `POST` the proof. Running the solver `python -u solve.py "Google:Pixel 7:33"` (saved in `soulvault/run1.txt`):

```console
$ python -u solve.py "Google:Pixel 7:33"
```

```text
GET 200 {"difficulty":20,"nonce":"7745e72075f3b08185931a912d3fc6c0","ticket":"b44856ea67b3388b463deece16834892"}
counter = 1783227  (10.0s, sha256 zero-bits=22)
POST 200 {"fragment_id":"2e76740874975b60","message":"OWASP{soul_vault_fragment_recovered}","status":"awakened"}
```

The device string matches the client-side check:

```text
sha256("Google:Pixel 7:33") = 0e71c95267c1f813a5870d5bff97f1aaf2ab3439fc52fa98f4ccd7a676a9b9ab
```

`POST 200` returns a `message` containing the flag. The run was reproduced a second time from a different device/client, returning `fragment_id 23c5aa7f88e9ef6a` with the same `message`.

## Result

```text
OWASP{soul_vault_fragment_recovered}
```

The flag was read from the live service: `POST /v1/soul/echo/fragment` returned a `message` containing the flag, and the result reproduced on a second client. No submission response recorded.

## Reproduce

The API must still be available. The saved solver models token function `p` and proof-of-work function `q`; its source and the full seed/four-round SHA-256 construction are not included, so this writeup currently documents the flow and saved output.
