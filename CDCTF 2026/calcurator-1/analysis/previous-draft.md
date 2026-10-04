---
title: "CalcuRATor (1/4)"
ctf: "CDCTF 2026"
date: 2026-10-04
category: "Forensics, Rev Eng"
difficulty: "Không được công bố"
points: 491
flag_format: "cdctf{processname}"
author: "Người giải trong phiên chat"
challenge_author: "reep236"
---

# CalcuRATor (1/4)

## Tóm tắt

Phân tích tĩnh ELF x86-64 cho thấy tiến trình con đổi tên hiển thị thành `wpad` bằng cách ghi đè `argv[0]`. Không cần chạy mẫu với quyền root.

## Lời giải

Dùng strings và objdump để tìm chuỗi `I’m not root :(` cùng mã daemon hóa. Sau `setsid()` và `chdir()`, tại `0xf0f7e` chương trình nạp chuỗi ở `0x5c832d`; tại `0xf0f8a` gọi `strncpy(argv[0], "wpad", strlen(argv[0]))`. Các đối số còn lại được ghi đè bằng dấu cách.

Đoạn mã sau trích xuất trực tiếp tên từ mẫu đã phân tích:

```python
from pathlib import Path
b = Path(r"C:\Users\Administrator\Downloads\calculator (1)").read_bytes()
name = b[0x5c832d:].split(b"\0", 1)[0].decode()
print(f"cdctf{{{name}}}")
```

Tên này là tên trong dòng lệnh do `argv[0]` bị sửa; bằng chứng ở đây không phải lời gọi `prctl(PR_SET_NAME)`.

## Mẫu và công cụ

File: `calculator (1)`, ELF 64-bit x86-64. SHA-256: `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`. Cả bốn file có cùng hash, nên các offset phân tích áp dụng cho cả bốn phần. Công cụ: Python 3.12, GNU objdump, phân tích strings; phần 4 thêm đối chiếu repository công khai. Toàn bộ lời giải dùng phân tích tĩnh.

## Flag

```text
cdctf{wpad}
```
