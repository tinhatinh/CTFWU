---
title: "CalcuRATor (2/4)"
ctf: "CDCTF 2026"
date: 2026-10-04
category: "Forensics, Rev Eng"
difficulty: "Không được công bố"
points: 500
flag_format: "cdctf{PROTOCOL PACKET TYPE}"
author: "Người giải trong phiên chat"
challenge_author: "reep236"
---

# CalcuRATor (2/4)

## Tóm tắt

Backdoor dùng raw socket để nhận ICMP và chỉ xét gói Echo Request.

## Lời giải

Hàm tại `0x12b460` thiết lập `socket(2, 3, 1)`, tương ứng `AF_INET`, `SOCK_RAW`, `IPPROTO_ICMP`. Dữ liệu được nhận bằng `recv()` vào bộ đệm tại `rsp+0x20`.

Tại `0x12b4c8`, chương trình so sánh byte `[rsp+0x34]` với `8`: đó là byte ở offset 20 tính từ đầu gói IPv4, tức trường type của ICMP sau header IPv4 20 byte. Type 8 là Echo Request. Gói còn cần vượt qua kiểm tra payload được giải trong phần 3.

Lệnh tái kiểm tra trên PowerShell, với GNU objdump trong PATH:

```powershell
objdump -d -M intel --start-address=0x12b460 --stop-address=0x12b536 'C:\Users\Administrator\Downloads\calculator (2)'
```

Các dấu hiệu quyết định: tham số `socket(2,3,1)` và phép so sánh type với `0x8`.

## Mẫu và công cụ

File: `calculator (2)`, ELF 64-bit x86-64. SHA-256: `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`. Cả bốn file có cùng hash, nên các offset phân tích áp dụng cho cả bốn phần. Công cụ: Python 3.12, GNU objdump, phân tích strings; phần 4 thêm đối chiếu repository công khai. Toàn bộ lời giải dùng phân tích tĩnh.

## Flag

```text
cdctf{ICMP ECHO REQUEST}
```
