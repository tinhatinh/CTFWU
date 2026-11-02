---
title: "Cold Circuit"
category: "Reverse"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Cold Circuit

## Đề bài

Binary checker x86-64 đã strip kiểm tra flag có phần thân ở dạng hex. Cần phân tích phép biến đổi trên input rồi đảo ngược để tìm chuỗi được chấp nhận.

## Phân tích

Input được đọc từ `argv[1]` hoặc stdin, phải có dạng `hiCTF{` + 32 ký tự hex + `}`, tổng cộng 39 ký tự. Routine tại `0x12d6` giải 32 ký tự hex thành 16 byte.

Binary gọi `ptrace(PTRACE_TRACEME)` khi khởi động. Nếu phát hiện đang bị trace, nó sửa `table[0][0] ^= 1`, làm sai bảng được copy từ `0x2140` lên stack. Vì vậy cần kiểm tra nghiệm cuối bằng một lần chạy không có debugger.

Hai nhánh tại `0x1229` và `0x125c` in `unreachable` hoặc trả mã 98 là nhánh giả. Điều kiện tương ứng đòi hỏi `x² + 1 ≡ 0 (mod 4)`, không thể xảy ra với số nguyên: bình phương modulo 4 chỉ có thể là 0 hoặc 1.

## Lời giải

### 1. Xác định mạch thật

Mỗi vòng biến đổi trạng thái 16 byte bằng ba thao tác khả nghịch:

1. Cộng modulo 256 với một hàng 16 byte trong bảng 320 byte tại `0x2140`.
2. Thay thế byte qua S-box 256 byte tại `0x2020`.
3. Hoán vị 16 vị trí theo bảng tại `0x2120`.

Sau 20 vòng, trạng thái được so với target 16 byte tại `0x2280`.

### 2. Đảo ngược từng vòng

Bắt đầu từ target. Với thứ tự vòng từ 19 về 0, áp dụng hoán vị nghịch đảo, S-box nghịch đảo rồi trừ hàng tương ứng modulo 256. Kết quả giải ngược được ghi lại ở dạng hex là `6e305f6a7461675f6e65656465642121`.

Chuỗi hex này giải mã thành:

```
n0_jtag_needed!!
```

### 3. Kiểm tra nghiệm

Đưa phần thân hex vào đúng định dạng flag rồi chạy checker bình thường. Bản ghi xác nhận cả hai cách truyền argv và stdin đều trả `Access granted.`.

## Kết quả

```
hiCTF{6e305f6a7461675f6e65656465642121}
```

Các địa chỉ trên thuộc binary của bài. Để dựng script đảo mạch cần trích đủ S-box, bảng cộng, bảng hoán vị và target từ chính binary đó.
