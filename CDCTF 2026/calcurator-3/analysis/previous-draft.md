---
title: "CalcuRATor (3/4)"
ctf: "CDCTF 2026"
date: 2026-10-04
category: "Forensics, Rev Eng"
difficulty: "Không được công bố"
points: 500
flag_format: "cdctf{Fl4g!}"
author: "Người giải trong phiên chat"
challenge_author: "reep236"
---

# CalcuRATor (3/4)

## Tóm tắt

Echo Request thông thường chưa đủ. Payload phải bắt đầu bằng khóa kích hoạt được che giấu bằng XOR.

## Lời giải

Sau khi kiểm tra ICMP type 8, tại `0x12b4cf` chương trình yêu cầu byte đầu payload, offset 28 của gói, bằng `0x63` (`c`). Vòng lặp tại `0x12b500` kiểm tra 19 byte tiếp theo bằng XOR với dữ liệu ở `0x5e700f`, rồi so sánh với dữ liệu ở `0x5c62db`.

Script hoàn chỉnh phục hồi khóa:

```python
from pathlib import Path
b = Path(r"C:\Users\Administrator\Downloads\calculator (3)").read_bytes()
target = b[0x5c62db:0x5c62db + 21]
key = b[0x5e700f:0x5e700f + 24]
trigger = b"c" + bytes(target[i - 1] ^ key[i] for i in range(2, 21))
print(trigger.decode())
```

Kết quả: `cdctf{1CMP_TR1GG3R$}`.

Sau khóa, mã còn đọc địa chỉ callback và cổng qua `sscanf(..., "%15s %d", ...)`; cổng phải dương và chuỗi địa chỉ phải dài ít nhất 7 ký tự. Vì vậy, để kích hoạt hành vi callback, payload còn cần thông tin này sau khóa và dấu cách. Flag yêu cầu khóa, không yêu cầu gửi gói hay thực thi backdoor.

## Mẫu và công cụ

File: `calculator (3)`, ELF 64-bit x86-64. SHA-256: `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`. Cả bốn file có cùng hash, nên các offset phân tích áp dụng cho cả bốn phần. Công cụ: Python 3.12, GNU objdump, phân tích strings; phần 4 thêm đối chiếu repository công khai. Toàn bộ lời giải dùng phân tích tĩnh.

## Flag

```text
cdctf{1CMP_TR1GG3R$}
```
