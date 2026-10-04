---
title: "CalcuRATor (4/4)"
ctf: "CDCTF 2026"
date: 2026-10-04
category: "Forensics, Rev Eng, OSINT"
difficulty: "Không được công bố"
points: 500
flag_format: "cdctf{calculator/tool}"
author: "Người giải trong phiên chat"
challenge_author: "reep236"
---

# CalcuRATor (4/4)

## Tóm tắt

Mẫu ghép CLI của Qalculate (`libqalculate`) với backdoor PRISM (`prism`), có chỉnh sửa tên tiến trình và cách kiểm tra khóa.

## Lời giải

### 1. Nhận diện calculator

Strings trong mẫu chứa `libqalculate`, `QALCULATE_USER_DIR`, `QALCULATE_DEFINITIONS_DIR`, `qalc` và URL tài liệu Qalculate. [Repository libqalculate](https://github.com/Qalculate/libqalculate) chứa CLI `qalc`; [man page](https://github.com/Qalculate/libqalculate/blob/master/man/qalc.1) xác nhận đây là giao diện dòng lệnh của Qalculate.

### 2. Đối chiếu backdoor với mã nguồn

[Mã nguồn prism.c](https://github.com/andreafabrizi/prism/blob/master/prism.c) có cùng chuỗi thao tác đặc trưng:

- `socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)` và bộ đệm 1024 byte.
- Kiểm tra `ICMP_ECHO` cùng khóa trong payload.
- Đọc callback bằng `sscanf(..., "%15s %d", bd_ip, &bd_port)`.
- Bỏ qua khi cổng không dương hoặc địa chỉ ngắn hơn 7 ký tự.
- `fork()` rồi tạo reverse shell bằng socket TCP, `dup2()` và `/bin/sh`.
- Sửa tên bằng `strncpy(argv[0], PROCESS_NAME, strlen(argv[0]))`, rồi xóa đối số còn lại bằng dấu cách.

Trong binary, parser và điều kiện nằm tại `0x12b55f–0x12b59b`; phần sửa tên nằm tại `0xf0f7e–0xf0fba`. Sự trùng khớp cả parser, điều kiện kiểm tra và cách đổi tên là bằng chứng cụ thể hơn việc chỉ cùng sử dụng ICMP.

Tên theo repository cần dùng trong flag là `libqalculate/prism`, dù chương trình calculator được gọi là `qalc`.

## Mẫu và công cụ

File: `calculator (4)`, ELF 64-bit x86-64. SHA-256: `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`. Cả bốn file có cùng hash, nên các offset phân tích áp dụng cho cả bốn phần. Công cụ: Python 3.12, GNU objdump, phân tích strings; phần 4 thêm đối chiếu repository công khai. Toàn bộ lời giải dùng phân tích tĩnh.

## Flag

```text
cdctf{libqalculate/prism}
```
