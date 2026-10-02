# Radio Silence — Hardware (Medium)

**Flag:** `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}`
**Máy chủ mục tiêu:** `https://web-0350e37b217a0cbc.web.h7tex.com`
**Tệp dữ liệu:** `capture.cf32` (kích thước 393544 B, mã băm sha256 `167a70fa…`) - Luồng dữ liệu giải mã băng gốc (interleaved float32 LE I/Q), tốc độ mẫu 1 Msps.

## Đề bài

Hệ thống ghi nhận phát xạ vô tuyến từ thiết bị không xác định: không có tài liệu kỹ thuật (datasheet), không có thông tin giao thức (protocol notes). 
Hệ thống cung cấp file ghi baseband nguyên bản kèm yêu cầu: "Read it back" (Đọc nó đi). Nhiệm vụ là phân tích và đo đạc các thông số của một giao thức truyền tin chưa rõ ràng từ tín hiệu thô.

## Phân tích ban đầu

Phân tích thông tin máy chủ:
```bash
$ curl -sS https://web-0350e37b217a0cbc.web.h7tex.com
file: capture.cf32 (chuẩn complex baseband, đan xen dữ liệu interleaved float32 I/Q, little-endian theo định dạng: I0 Q0 I1 Q1 ...)
sample rate (tốc độ lấy mẫu): 1000000 Hz
```

Tải và đọc dữ liệu qua Python:
```python
raw = np.fromfile('files/capture.cf32', dtype='<f4')   # Nhận được 49193 mẫu, kéo dài 49.193 mili-giây
iq  = raw[0::2] + 1j*raw[1::2]
```

Bước đầu tiên là phân biệt phương pháp điều chế: Điều chế biên độ (AM) hay Điều chế tần số (FM). Biểu đồ phân bố (histogram) của `abs(iq)` cho thấy 2 nhóm tín hiệu: một nhóm tập trung ở 0 và một nhóm tập trung ở 1.0. Tín hiệu này mang đặc điểm của OOK (On-Off Keying). Kiểm tra độ dài dải sóng qua ngưỡng `abs > 0.35`, giả thuyết này bị bác bỏ:

```text
Tổng số mảng chạy (runs) bắt được: 5
Mảng từ      0 đến  2909: Nhóm 0      - mức nhiễu nền
Mảng từ   2909 đến 43200: Nhóm 1      - Khối tín hiệu liên hồi, biên độ (envelope) ổn định
Mảng từ  46109 đến   151: Nhóm 0
Mảng từ  46260 đến     1: Nhóm 1      - Tín hiệu đơn
Mảng từ  46261 đến  2932: Nhóm 0      - Khoảng tĩnh cuối
```

Đường bao biên độ (envelope) ổn định liên tục trong 43200 mẫu, đồng nghĩa tín hiệu mức "0" chỉ là tín hiệu tĩnh không có phát xạ. Đường bao biên độ không thay đổi và có sóng mang liên tục là đặc điểm của kỹ thuật FSK.

Xử lý khối tín hiệu qua thuật toán FFT (sử dụng cửa sổ Hanning, độ phân giải 23.1 Hz), hiển thị hai đỉnh tần số:

```text
Điểm +35.00 kHz  tại  0.00 dB
Điểm +84.99 kHz  tại -2.68 dB
```

Kết luận: Dải tone thực tế mang tần số 35 kHz và 85 kHz. Kết quả: sóng mang (carrier) nằm tại 60 kHz, với độ lệch pha sai số (deviation) là ±25 kHz.

## Chuỗi khai thác

### Bước 1: Tính toán chu kỳ symbol từ tín hiệu

Sử dụng discriminator theo công thức `diff(unwrap(angle(burst))) * fs / 2π`, áp dụng thuật toán làm mượt với cửa sổ 8 mẫu. Phân tích histogram cho thấy hai cụm tín hiệu rạch ròi tại 35 kHz và 85 kHz. Các tín hiệu nhiễu ở khoảng giữa là các mẫu đang chuyển trạng thái (transition).

Phân tích tần suất chuyển mạch và tính toán modulo để tìm chu kỳ:

```text
Danh sách các ứng viên chu kỳ symbol tốt nhất:
Trị số 0.552  ứng với S=100  kéo 100.0 us  chạy 10000.0 baud
Trị số 0.552  ứng với S= 50   kéo 50.0 us  chạy 20000.0 baud      (Đây là tín hiệu tương quan của S=100)
Trị số 0.552  ứng với S= 25   kéo 25.0 us  chạy 40000.0 baud
...
Đỉnh tín hiệu (tính bằng Hz): [10001.9, 20003.7, ...]
```

Kết luận: S=100 là thông số gốc (các giá trị khác chỉ là tương quan pha). Chuỗi xung transition tạo tín hiệu ở mốc 10 kHz. Với tốc độ 10 kBaud, khối tín hiệu dài 43200 mẫu truyền tải được `43200/100 = 432 symbol = 54 byte` chính xác.

Dữ liệu này loại trừ giả thuyết mã Manchester: Một nửa chu kỳ Manchester chiếm 100 mẫu thì yêu cầu hệ thống khi đạt biên 100 mẫu phải chuyển mạch (ghi nhận ít nhất ≥431 phát). Trong khi đó, bộ discriminator chỉ ghi nhận đổi mức 248 lần trên 431 đường biên (tương đương 50% mật độ chuỗi dữ liệu ngẫu nhiên ở 10 kBaud).

### Bước 2: Giải mã symbol

Sử dụng nguyên tắc đa số phân tích 80 mẫu ở giữa mỗi chu kỳ 100 mẫu, nếu mức tín hiệu là 85 kHz, ghi nhận bit 1 (ưu tiên MSB-first):

```python
states = (sm > 60e3).astype(np.int8)
slots  = [states[i*100+10:(i+1)*100-10] for i in range(432)]
bits   = np.array([s.mean() > 0.5 for s in slots], dtype=np.uint8)
frame  = np.packbits(bits).tobytes()
```

```text
[*] Kiểm tra giá trị   mức margin tối thiểu đạt 0.500, không có 0/432 khoang nào có margin < 0.05
[*] Khung dữ liệu trả về: aaaaaaaaaaaa2dd42b48374354467b36373830383536642d646234322d346366612d386235362d6336323130396438343137637d7a65
[*] Chuyển mã sang ascii: b'\xaa\xaa\xaa\xaa\xaa\xaa-\xd4+H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}ze'
[*] Dữ liệu dư thừa    0 bit cuối cùng
```

Giá trị `min margin 0.500` chứng minh độ tin cậy cao: không có hiện tượng can nhiễu tone nên việc đọc bit là tuyệt đối.

### Bước 3: Loại trừ các sai số

Trường hợp cấu hình giải mã:

```text
t85=1 nạp MSB   : Ký tự in được 46/54  -> Văn bản hợp lệ b'\xaa\xaa...H7CTF{6780856d-db42-...'
t85=1 nạp LSB   : Ký tự in được 25/54  -> Dữ liệu không hợp lệ
t35=1 nạp MSB   : Ký tự in được  7/54  -> Dữ liệu không hợp lệ
t35=1 nạp LSB   : Ký tự in được 18/54  -> Dữ liệu không hợp lệ
```

## Giải mã cấu trúc frame

| Phân vùng | Byte | Mô tả |
| --- | --- | --- |
| Preamble | `aa aa aa aa aa aa` | Tương đương với chuỗi `0b10101010`, dạng sóng đồng bộ hóa xung nhịp đồng hồ. |
| Header | `2d d4 2b` | Chưa xác định, có khả năng là định danh kết hợp với mã nhóm lệnh. |
| Payload | `48 37 43 54 46 7b … 7d` | Trích xuất cờ `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}` (chiếm 43 B) |
| Trailer | `7a 65` | Đoạn dữ liệu không giải mã được: Thử checksum `sum8=0x9f`, `xor8=0xf7`, sử dụng CRC16-CCITT = `0xdeea`/`0xd655`, hoặc CRC16 reflected = `0x2d08`/`0x9657`, các phương pháp trên đều không cho ra mã `0x7a65`. Khả năng cao đây là dữ liệu không hợp lệ hoặc nonce ngẫu nhiên. |

Lưu ý hệ thống không gửi cờ qua HTTP: Hệ thống chỉ cung cấp file dữ liệu tĩnh (`Server: SimpleHTTP/0.6`), không có giao diện submit form. Yêu cầu gửi cờ trực tiếp lên hệ thống chấm điểm CTF.

## Flag
```bash
$ python solve_rf.py files/capture.cf32
[+] FLAG: H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}
```
