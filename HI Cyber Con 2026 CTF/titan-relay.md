---
title: "Titan Relay"
category: "Pwn"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Titan Relay

## Đề bài

Relay console viết bằng Rust, định dạng PE32+, chạy dưới Wine và thực thi input trong một VM nhỏ. Mục tiêu là dựng một order hợp lệ để VM mở file flag.

## Phân tích

Input gồm độ dài capsule từ 1 đến 512, sau đó là các byte hex. Trước khi thực thi, mỗi byte được XOR với `(0x71 + 0x3d*i) & 0xff`.

Context của VM có các vùng:

| Vị trí | Nội dung |
|---|---|
| `ctx+0x18` | 8 thanh ghi |
| `ctx+0x58` | 16 ô nhớ |
| `ctx+0xd8` | Bảng đặc biệt: `cookie_lo`, `cookie_hi`, `cookie^func`, 0 |
| `ctx+0x8` | Integrity field phải bằng cookie |
| `ctx+0x10` | Integrity field phải bằng `&0x1400018c0` |

Opcode store `0x32` dùng chỉ số có dấu. Kiểm tra biên cho phép index âm, khiến phép ghi đi ngược khỏi vùng `mem` vào các integrity field.

## Lời giải

### 1. Khôi phục cookie và function pointer

Đọc các entry 0–2 của bảng đặc biệt. Ghép `cookie_hi` và `cookie_lo` thành cookie 64 bit, rồi XOR entry `cookie^func` với cookie để lấy function pointer.

### 2. Ghi integrity field qua index âm

Instruction `0x32` ghi một dword từ thanh ghi A tới `mem[imm16] + D*4`. Với `imm16=-10` hoặc `-9`, các lần ghi chạm vào hai integrity field nằm trước vùng nhớ VM. Ghi đúng cookie và pointer vừa khôi phục để vượt kiểm tra.

### 3. Dựng order rồi halt

Đặt order trong `mem[0..]`, với đường dẫn đã XOR theo cookie. Trỏ register 6 tới `&mem[0]`, sau đó kết thúc bằng opcode `0x51` để chuyển sang xử lý order.

Đường dẫn được dựng là `Z:\flag.txt`. Trong Wine, ổ `Z:` ánh xạ tới gốc filesystem của môi trường bài, nên đường dẫn này truy cập `/flag.txt`.

## Kết quả

```
hiCTF{ru5t_vm_g4te_and_h4ndler_ch41n_5e8259594d}
```

Bản lưu mô tả primitive ghi cùng cách dựng order; không kèm đầy đủ assembler capsule và layout các field của order để tái hiện độc lập. Cần binary gốc hoặc solver của lần chạy để điền các chi tiết còn lại.
