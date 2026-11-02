---
title: "ChronoGrind"
category: "Crypto"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# ChronoGrind

## Đề bài

Bài cung cấp `state.dat` cùng container mã hóa `CGFX`. Cần tính trạng thái 256 byte sau chín tỷ vòng lặp, lấy `SHA-256(v)` làm khóa rồi giải mã ChaCha20-Poly1305 để thu flag.

## Phân tích

Container có bố cục:

```
"CGFX" | version (1 byte) | nonce (12 bytes) | Poly1305 tag (16 bytes) | ciphertext
```

Điểm cần xác định trước khi chạy phần tính toán dài là vị trí authentication tag: tag 16 byte nằm trước ciphertext. Khóa được suy ra từ toàn bộ giá trị trạng thái `v`, không phải chuỗi ký tự biểu diễn nó. Bản ghi đã kiểm tra định dạng bằng một vòng mã hóa rồi giải mã dữ liệu tổng hợp trước khi chạy trên artifact thật.

## Lời giải

### 1. Tính trạng thái

Chạy vòng lặp của bài đến mốc `9,000,000,000`. Tốc độ được ghi nhận khoảng 1,1 triệu vòng/giây. `state.dat` cung cấp thông tin cần để theo dõi trạng thái; bản tóm tắt không chứa đầy đủ hàm chuyển trạng thái nên không đủ để tự dựng lại vòng lặp từ đầu.

### 2. Suy ra khóa và xác thực

Lấy SHA-256 của trạng thái 256 byte thu được, parse nonce/tag/ciphertext theo bố cục trên rồi giải mã ChaCha20-Poly1305. Kết quả đã lưu:

```
it=9000000000 (100.000%) rate=1139690/s eta=0 s
DONE
SUCCESS v:sha256-be|tag-before-ct
b'hiCTF{n1c3_w0rk_n0w_t4k3_s0m3_r3$t}'
FLAG: hiCTF{n1c3_w0rk_n0w_t4k3_s0m3_r3$t}
EXIT=0
```

Thông báo `SUCCESS v:sha256-be|tag-before-ct` ghi lại biến thể biểu diễn trạng thái và vị trí tag đã giải mã thành công. Đây là bằng chứng từ lần chạy, không phải một định nghĩa đầy đủ cho thuật toán grind.

## Kết quả

```
hiCTF{n1c3_w0rk_n0w_t4k3_s0m3_r3$t}
```

Để tái hiện toàn bộ cần artifact gốc và implementation của vòng lặp; bộ writeup hiện chỉ giữ bố cục container cùng output cuối.
