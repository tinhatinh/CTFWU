---
title: "Labyrinth"
category: "Misc"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Labyrinth

## Đề bài

Service dùng giao thức nhị phân không có tài liệu để mở một mê cung. Cần khôi phục handshake, giải challenge/response rồi gửi đường đi đúng đến sealed gate. Lối thoát dễ thấy chỉ trả flag giả.

## Phân tích

Mỗi frame gồm magic, opcode một byte, độ dài body hai byte big-endian và body:

```
LBY\x7f | opcode (1 byte) | body length (2 bytes, big-endian) | body
```

Lưu ý ký hiệu `\\x7f` ở bản ghi biểu diễn byte magic `0x7f`, không phải bốn ký tự văn bản gửi lên socket.

## Lời giải

### 1. Hoàn tất handshake

Gửi opcode `0x01` (`HELLO`) để nhận server nonce. Sau đó gửi `0x10` (`PROBE`) kèm nonce để lấy challenge dài 28 byte.

### 2. Tính response

Lấy hai đoạn bốn byte trong challenge và XOR sau khi đảo thứ tự đoạn cuối:

```
k  = challenge[4:8]
w6 = challenge[24:28]
answer = k XOR reverse(w6)
```

Gửi response bốn byte bằng opcode `0x30`. Khi response hợp lệ, server mở phần mê cung.

### 3. Khôi phục đường đi tới sealed gate

Response của mỗi phòng chứa `x, y, exit_mask, flag, token`. Các bit hướng trong `exit_mask` là `N=1, E=2, S=4, W=8`. Dùng tọa độ cùng các cửa mở để dựng đồ thị và tìm đường ngắn nhất từ cửa vào tới sealed gate.

Tại sealed gate, gửi opcode `0x30` kèm đường đi. Mỗi bước là một byte theo mã:

```
N=0, E=1, S=2, W=3
```

Độ dài route bằng số bước. Không dùng opcode `0x40` để kết thúc: nó trả `hiCTF{not_the_exit}`. Field tên `flag` ở các phòng thông thường cũng là mồi nhử; flag thật đến từ response kiểm tra route tại sealed gate.

## Kết quả

```
hiCTF{l34rn3d_th3_t0ngu3_w4lk3d_th3_l4byr1nth_2b3f484331}
```

Bản lưu mô tả framing và cách tính response nhưng không kèm toàn bộ client hay route cụ thể của lần chạy.
