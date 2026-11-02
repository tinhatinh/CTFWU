---
title: "Rocinate"
category: "Crypto"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Rocinate

## Đề bài

Bài công bố 102 output liên tiếp từ `random.randint(1, N)` của Python: `a`, `b` và `C_0..C_99`. Mục tiêu là khôi phục trạng thái MT19937, suy ra các giá trị bị giấu và giải quan hệ lũy thừa chứa secret.

## Phân tích

Phải mô hình hóa đúng phép sinh số: `random.randint(1, N)` tương ứng `1 + _randbelow(N)`. Giá trị tương ứng output sinh ngẫu nhiên vì thế là `value - 1`.

Với kích thước số trong bài, mỗi lần lấy ứng viên tiêu thụ 64 word MT: 63 word 32 bit và một word 31 bit. Bước rejection của `_randbelow` có thể tiêu thụ thêm ứng viên, nên không thể tùy ý xem mọi output công khai là các khối liên tục không có khoảng trống.

## Lời giải

### 1. Tìm cửa sổ không có rejection

Dùng quan hệ truy hồi có độ trễ 624 word của MT19937 để tìm cửa sổ 10 lần lấy số không có rejection. Đây là điểm neo để ghép các word vào đúng vị trí trạng thái.

### 2. Khôi phục và tua ngược trạng thái

Dùng khối tiếp theo để giải các bit thấp bị thiếu. Sau đó mở rộng trạng thái về trước từng word bằng hai phương trình truy hồi liên tiếp; bit 31 còn thiếu quyết định nhánh cần chọn. Khi trạng thái đã được khôi phục, `r` tương ứng lần sinh đầu tiên của chuỗi.

### 3. Khôi phục secret

Tính các `R_i` từ LCG của đề, rồi chọn một cặp số mũ `(C_i, C_j)` nguyên tố cùng nhau. Đẳng thức Bézout cho các hệ số kết hợp hai giá trị dạng `s^{C_i}` để khôi phục `s` trong nhóm đang xét.

Đối chứng đã lưu là `T_i == R_i^e` đúng cho cả 100/100 phần tử rò rỉ, giúp kiểm tra trạng thái khôi phục trước khi lấy flag.

## Kết quả

```
hiCTF{lmaoooo_w0t???y0u_d1d_17_??435p37++}
```

Bản lưu hiện không chứa đầy đủ `N`, tham số LCG, các output công khai và mã giải hệ bit. Đây là mô tả phương pháp cùng kết quả đã thu được; cần dữ liệu đề và implementation tương ứng để chạy lại toàn bộ phép khôi phục.
