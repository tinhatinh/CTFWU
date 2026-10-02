# Open Sesame — Hardware (Hard)

**Flag:** `H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}` (Máy chủ trả về qua cổng `/unlock`, lưu tại file `flag.txt`)
**Mục tiêu:** `https://web-7a56034b5423964c.web.h7tex.com` 
**Artifact:** `capture.cf32` (Luồng dữ liệu băng gốc baseband định dạng I/Q float32 little-endian, tốc độ mẫu 1 MHz)

## Đề bài

Mục tiêu là phân tích tín hiệu từ một remote điều khiển cửa gara thông dụng. Đặc tính của thiết bị là mỗi lần kích hoạt, nó phát ra một chuỗi mã mới. Hệ thống cung cấp bản ghi băng gốc (baseband) của 8 lần bấm phím liên tiếp. Kèm theo là một ghi chú quan trọng: "Cái không đoán ngẫu nhiên được (unguessable) không có nghĩa là cái không tính trước được (unpredictable)". 
Nhiệm vụ: Tính toán dải mã mà thiết bị sẽ phát ra ở lần kích hoạt thứ 9 và gửi mã đó lên máy chủ để mở khóa.

## Phân tích ban đầu

Phân tích tệp `capture.cf32`: Đây là tín hiệu I/Q định dạng float32, kiến trúc little-endian (LE), lấy mẫu ở tần số 1 MHz. Do môi trường làm việc bị hạn chế về phần mềm (không có GNU Radio hay urh), quá trình giải mã tín hiệu (demodulate) được thực hiện bằng script cục bộ.

## Quá trình khai thác

**Bước 1 - Trích xuất đường bao biên độ (Envelope).** 
Áp dụng công thức cơ bản `env = I^2 + Q^2` để lấy đường bao. Tuy nhiên, tín hiệu thô có biên độ nhiễu (ripple) lớn, yêu cầu xử lý qua một bộ lọc làm mượt (smoothing) với cửa sổ kích thước 20 micro-giây cho mỗi đơn vị chip (chu kỳ bit cơ sở).

**Bước 2 - Thiết lập ngưỡng phân định OOK.** 
Tính toán ngưỡng cắt biên độ theo phương trình `p1 + 0.35*(max - p1)`. Sau khi cắt tín hiệu, hệ thống nhận diện được 392 khối phát sóng (burst).

**Bước 3 - Phân tách tín hiệu thao tác.** 
Phân tích khoảng nghỉ giữa các luồng truyền tín hiệu, lấy mốc thời gian im lặng dài hơn 1.5 mili-giây để chia khối dữ liệu. Quá trình này chia dải sóng ra thành 8 cụm thao tác bấm riêng biệt (cách nhau bởi 7 khoảng nghỉ dài khoảng ~10 chu kỳ T).

**Bước 4 - Phân tích chuỗi bit nội bộ.** 
Cấu trúc độ dài chạy mã (run-length) rất cơ bản, quy định 2 ngưỡng: 1T và 2T (với mỗi chu kỳ T bằng 303 micro-giây). Mỗi cụm mã bao gồm 97 khoảng (run), theo phương trình `1 + 2×48` -> tương đương 48 bit dữ liệu. Mỗi bit được biểu diễn qua hai trạng thái (High, Low): Cấu trúc `H1L2` đại diện bit 0, `H2L1` đại diện bit 1.

**Bước 5 - Giải mã 8 khung sóng (Frame).**
Sau quá trình xử lý, trích xuất được 8 dải mã hex tĩnh:

```text
4f122809be13
4f122809c117
4f122809c41a
4f122809c71d
4f122809ca10
4f122809cd13
4f122809d017
4f122809d31a
```

**Bước 6 - Phân tách dữ liệu mã lặp (Rolling code).** 
Cấu trúc dải 48 bit (12 ký tự hex) được phân chia thành ba phần: `32 bit cố định | 12 bit biến đếm (counter) | 4 bit checksum (crc)`:

| Lần kích hoạt | Biến đếm (counter) | CRC đuôi | Phép tính (mod 16) tổng của 11 nibble đầu |
| --- | --- | --- | --- |
| 0 | 0xbe1 | 3 | 3 |
| 1 | 0xc11 | 7 | 7 |
| 2 | 0xc41 | a | a |
| 3 | 0xc71 | d | d |
| 4 | 0xca1 | 0 | 0 |
| 5 | 0xcd1 | 3 | 3 |
| 6 | 0xd01 | 7 | 7 |
| 7 | 0xd31 | a | a |

Quy luật phân tích:
- Biến đếm counter tăng dần theo quy luật `+0x30` sau mỗi thao tác bấm.
- Thuật toán CRC tính toán đơn giản: `crc = (tổng giá trị của 11 cụm 4 bit đầu tiên) mod 16`. Công thức này khớp chính xác với 8 khung dữ liệu.

Cơ chế tạo chuỗi mã mới thực chất là sự thay đổi của biến đếm counter kết hợp CRC đơn giản. Gợi ý "unguessable ≠ unpredictable" chỉ ra chính xác lỗ hổng bảo mật trong cấu trúc tạo mã ngẫu nhiên của thiết bị.

**Bước 7 - Tính toán tham số lần kích hoạt 9.**
Thực hiện tính toán với công thức đã thu thập:

```text
Bước counter = 0xd31 + 0x30 = 0xd61
Khung thân    = 4f122809 d61  + crc
Toán crc      = (4+15+1+2+2+8+0+9 + 13+6+1) mod 16 = 61 mod 16 = 13 = d (hệ hex)
Dải mã cuối   = 4f122809d61d
```

**Bước 8 - Kiểm chứng quy luật.** 
Cả hai quy luật (phần mã tĩnh và mức tăng biến đếm) được kiểm chứng qua 8 khung mã thu nhận độc lập, giảm thiểu xác suất ngẫu nhiên. Đoạn mã cố định 32 bit không đổi ở mọi khung, khoảng cách biến đếm counter giữ cố định `0x30`, và thuật toán CRC trả về kết quả chính xác cho chuỗi mã crc cuối.

## Flag
```bash
python solve.py https://web-7a56034b5423964c.web.h7tex.com analysis/capture.cf32 --submit
```

Phản hồi API:
```text
[*] Gõ cửa /unlock -> Nhận mã 200 OK
{"status": "unlocked", "flag": "H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}"}
```
