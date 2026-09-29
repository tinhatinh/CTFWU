---
title: "Loose Ends — Pwn (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Pwn]
tags: [h7ctf-quals, Pwn]
image:
  path: /CTFWU/H7CTF%202026%20Quals/loose-ends/files/de.png
---
{% raw %}
**Flag:** `H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}` · 248 pts · H7TEX 2026
**Target:** `pwn.h7tex.com:42589` · **Files:** `ledger.zip` → `ledger` (ELF x86-64), `libc.so.6` (glibc 2.39-0ubuntu8.9), `ld-linux-x86-64.so.2`

## Đề bài

Sổ cái của Sparrow Freight. Người ghi sổ xoá các mục cũ không kỹ như họ tưởng, và có một bản
audit đọc to mã thông hành trong ngày mà từ trước tới giờ chưa ai gọi nó. Nối các loose ends lại.

## Phân tích ban đầu

```
ET_EXEC no PIE | NX on | canary có (menu/idx/audit)
GNU_RELRO 0x403df8..0x404000  ->  mọi JUMP_SLOT hàm ở 0x404000..0x404060 vẫn ghi được
```

`main` là menu 4 lựa chọn trên một mảng con trỏ toàn cục:

```
notes[16] @ 0x4040a0
add    : notes[i] = malloc(0x50); read(0, notes[i], 0x50)
delete : free(notes[i])                      <- không notes[i] = NULL
edit   : if (notes[i]) read(0, notes[i], 0x50)
view   : if (notes[i]) write(1, notes[i], 0x50)
```

`delete` để lại con trỏ đã giải phóng, còn `edit`/`view` chỉ kiểm tra con trỏ khác 0: use-after-free cả
đọc lẫn ghi.

`audit @ 0x4012b6` mở `/flag`, đọc 80 byte rồi `printf("[audit] %s\n", ...)`. Nó không có trong jump
table của menu, nên cách duy nhất tới nó là nhảy.

Hai chi tiết làm bài dễ hơn dự kiến. Heap không random hoá: cấp phát đầu tiên nằm ở `0x4062b0`, ngay sau
BSS. RELRO cắt tại `0x404000`: toàn bộ GOT của PLT ghi được, và không PIE nên không cần leak gì cả.

## Các hướng đã loại

1. Gọi `audit` bằng input. Không có nhánh nào của menu trỏ tới nó, nên không có tổ hợp lựa chọn nào
   gọi được. Chỉ còn hướng ghi đè một GOT slot đang dùng rồi để chương trình tự nhảy.
2. Phải leak libc rồi mới tính tiếp. `audit` và mọi GOT slot đều là địa chỉ cố định vì binary là
   `ET_EXEC` không PIE, heap cũng cố định vì chunk đầu ở `0x4062b0`. Thứ duy nhất phải lấy là
   `heap >> 12`, và nó nằm ngay trong tcache (Bước 1).
3. Nhắm `free@GOT` ở `0x404000`. Khi pop một entry, glibc ghi ngược `next`/`key` vào chunk vừa cấp.
   Nhắm `0x404000` thì cú ghi thừa đó chạm `puts@GOT` ở `0x404008`, mà menu gọi `puts` ngay vòng lặp kế
   tiếp. `exit@GOT` (`0x404060`) đẩy cú ghi thừa xuống `0x404060+8` thuộc `.data`, vô hại. Nên slot
   đích là `0x404060`.

## Chuỗi khai thác

**Bước 1 - Leak `heap >> 12` để thắng safe-linking.** glibc 2.39 mã hoá con trỏ trong tcache:
`stored = (pos >> 12) ^ real`. Khi `free(A)` với A là phần tử cuối của bin thì `real = NULL`, nên 8 byte
đầu của A chính là `A >> 12`.

```
add(0); add(1); delete(0); view(0)   ->  8 byte đầu = 06 04 00 ...  =>  t = 0x406
```

**Bước 2 - Poison fd.** `delete(1)` đưa B lên đầu bin. `edit(1)` là UAF write, ghi đè chính `B->next`:

```python
edit(1, p64(t ^ 0x404060))     # 0x404060 = exit@GOT
```

B và A cùng trang nên `B >> 12 == t`, do đó khi `tcache_get` unmangle:
`(B>>12) ^ (t ^ 0x404060) = 0x404060`.

**Bước 3 - Hai lần cấp phát để lấy con trỏ.** `add(2)` pop B, `add(3)` pop `0x404060` →
`notes[3] = exit@GOT`. Kiểm chứng bằng `view(3)`: 80 byte in ra chứa `0x7f91ca0054c0` / `0x7f91ca0048e0`
(stdout/stdin) và `0x4062b0` / `0x406310` (notes[0], notes[1]) đúng như bố trí trong BSS.

**Bước 4 - Ghi `audit` vào `exit@GOT` rồi kích hoạt.**

```python
edit(3, p64(0x4012b6))     # read() chỉ lấy đúng số byte gửi lên -> chỉ 8 byte bị ghi
shutdown(SHUT_WR)          # menu: fgets(stdin) trả NULL -> exit(0) -> jmp audit
```

Đóng chiều ghi của socket làm `fgets` trả NULL, menu đi vào `exit`, và `exit` giờ là `0x4012b6`.

## Reproduce

```
python -u exploit.py pwn.h7tex.com 42589
```

`exploit.py` chỉ dùng `socket` + `struct`, tự sinh không cần libc leak.

## Flag
```
[audit] H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}
```

{% endraw %}
