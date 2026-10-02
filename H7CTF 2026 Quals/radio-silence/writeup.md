# Radio Silence — Hardware (Medium)

**Flag:** `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}`
**Máy chủ mục tiêu:** `https://web-0350e37b217a0cbc.web.h7tex.com`
**Tệp đồ nghề:** `capture.cf32` (kích thước 393544 B, mã băm sha256 `167a70fa…`) - Luồng dữ liệu giải mã băng gốc (interleaved float32 LE I/Q), tốc độ mẫu 1 Msps.

## Đề bài

Hệ thống ghi nhận được một đợt sóng vô tuyến (burst) bùng phát ngay sát một thiết bị lậu mà không ai biết tên: sạch bong không giấy tờ kỹ thuật (datasheet), không một dòng chú thích giao thức (protocol notes), thậm chí nhãn mác cũng trống trơn. 
Đề bài chỉ quăng cho ta một đoạn ghi baseband trần trụi kèm lời thách thức ngắn gọn: "Read it back" (Đọc nó đi). Điều này đồng nghĩa với việc ta phải trầy da tróc vẩy đi lùng sục, đo đạc bằng tay toàn bộ thông số của một giao thức truyền tin ma quái chỉ từ đống tín hiệu thô.

## Phân tích ban đầu

Móc ngoéo với máy chủ:
```bash
$ curl -sS https://web-0350e37b217a0cbc.web.h7tex.com
file: capture.cf32 (chuẩn complex baseband, đan xen dữ liệu interleaved float32 I/Q, little-endian theo định dạng: I0 Q0 I1 Q1 ...)
sample rate (tốc độ lấy mẫu): 1000000 Hz
```

Khai nòng đạn bằng Python:
```python
raw = np.fromfile('files/capture.cf32', dtype='<f4')   # Vớt được 49193 vạch mẫu, kéo dài 49.193 mili-giây
iq  = raw[0::2] + 1j*raw[1::2]
```

Nút thắt đầu tiên phải gỡ là xác định danh tính kẻ thù: Điều chế biên độ (AM) hay Điều chế tần số (FM). Nhìn qua biểu đồ phân bố (histogram) của `abs(iq)` thấy nổi lên hai rặng phong trào: một cụm xúm xít quanh mốc 0 và một đám xúm quanh mốc 1.0. Hình thái này bốc mùi sặc sụa của chiêu bài OOK (Chính một bài khác trong giải này cũng xài trò 433 MHz OOK/Manchester). Nhưng khoan, mổ băng kiểm tra độ dài chuỗi chạy (run-length) lọt qua khe cổng `abs > 0.35` thì cái giả thuyết lôm côm đó bị tát thẳng mặt:

```text
Tổng số mảng chạy (runs) bắt được: 5
Mảng từ      0 đến  2909: Nhóm 0      - Khoảng im lặng chết chóc đầu burst (mức nhiễu nền noise floor)
Mảng từ   2909 đến 43200: Nhóm 1      - Khối burst liên hồi cắn chặt, đường bao biên độ (envelope) lì lợm không đổi
Mảng từ  46109 đến   151: Nhóm 0
Mảng từ  46260 đến     1: Nhóm 1      - Dấu vết (blip) đơn độc mồ côi
Mảng từ  46261 đến  2932: Nhóm 0      - Vệt tĩnh lặng chốt đuôi
```

Đường bao biên độ (envelope) bám dính nằm lì phẳng lì suốt một dải 43200 mẫu, đồng nghĩa phần vạch "0" chẳng qua là màn đen im lặng hụt hơi trước và sau luồng phát xạ. Một khi đường bao nằm im không nhúc nhích + kèm theo sóng mang = Đó đích thị là trò biến tấu tần số 2-FSK.

Quăng khối burst thuần khiết đó qua lăng kính phân tích FFT (sử dụng cửa sổ Hanning, độ phân giải sắc bén 23.1 Hz), chồi lên hai ngọn núi đơn côi:

```text
Điểm +35.00 kHz  neo ở mức  0.00 dB
Điểm +84.99 kHz  neo ở mức -2.68 dB
```

Điều kỳ diệu là cả hai ngọn núi đâm chọc vào chính giữa khoang chứa (bin). Lật ngửa quân bài: Dải tone thực tế mang tần số 35 kHz và 85 kHz. Hệ quả tất yếu: sóng mang (carrier) ngự ở điểm cực 60 kHz, với độ lệch pha đung đưa (deviation) là ±25 kHz.

## Chuỗi khai thác

### Bước 1: Bắt mạch thời gian symbol từ bụng tín hiệu

Bơm bộ phát hiện biên (discriminators) chạy bằng thuật toán `diff(unwrap(angle(burst))) * fs / 2π`, phủ thêm màng bọc làm trơn với cửa sổ rộng 8 mẫu. Trải mớ đó lên histogram, giờ đây chỉ còn tóm được hai cụm (vây quanh biên 35 và 85 kHz) - đây là bảo chứng sắt đá cho 2 mức tần số thực. Đám râu ria dạt ra ở khoảng trống giữa hai cụm chính là đám mẫu đang cọ quậy đổi mức chuyển trạng thái (transition).

Thống kê tần suất vị trí chuyển trạng thái (transition) rồi đem đi xoay chia lấy phần dư (modulo) để rà tìm chu kỳ ứng cử viên:

```text
Danh sách các ứng viên đoạt giải chu kỳ symbol mượt nhất (best symbol-period candidates):
Trị số 0.552  ứng với S=100  kéo 100.0 us  chạy 10000.0 baud
Trị số 0.552  ứng với S= 50   kéo 50.0 us  chạy 20000.0 baud      (Đây chỉ là cái bóng đổ hoà âm ảo của S=100)
Trị số 0.552  ứng với S= 25   kéo 25.0 us  chạy 40000.0 baud
...
Đỉnh phổ của chuỗi tín hiệu lật mạch (top transition-train lines đo bằng Hz): [10001.9, 20003.7, ...]
```

Khoá mục tiêu: S=100 chính là hạt nhân chu kỳ cơ bản (đám 50/25/10 chỉ là những tiếng vọng hài hoà phái sinh từ một cái lưới pha duy nhất). Kèm theo đó, chuỗi xung transition khạc ra vạch phổ đóng đinh ở đúng mốc 10 kHz. Với con số 10 kBaud này, khối burst dài 43200 mẫu sẽ tải được lượng hàng hoá `43200/100 = 432 symbol = 54 byte` (chẵn như vắt chanh).

Dữ kiện này như một nhát búa đập vỡ cái giả thuyết xài mã Manchester: Phân nửa chu kỳ Manchester gánh 100 mẫu thì ép buộc hệ thống cứ chọc vào biên 100 mẫu là PHẢI nhảy chuyển mạch một phát (tức là gom hụi tối thiểu ≥431 phát). Trong khi đó, bộ dò discriminators lười biếng chỉ chịu nhảy nhót đổi mức có 248 phát chạy trên 431 cái đường biên symbol (chỉ ngang ngửa 50% mật độ nhảy của một chuỗi dữ liệu rác ngẫu nhiên chạy ở 10 kBaud).

### Bước 2: Ép cung từng symbol một

Xài chiêu bài dân chủ (Majority vote) bóc lột trên 80 mẫu nằm giữa mỗi khoang 100 mẫu, áp luật: hễ dính tone 85 kHz = chốt là số 1, ưu tiên nạp theo MSB-first:

```python
states = (sm > 60e3).astype(np.int8)
slots  = [states[i*100+10:(i+1)*100-10] for i in range(432)]
bits   = np.array([s.mean() > 0.5 for s in slots], dtype=np.uint8)
frame  = np.packbits(bits).tobytes()
```

```text
[*] Soi phiếu (decisions)   mức margin hẹp nhất (min margin) đạt 0.500, tuyệt nhiên 0/432 khoang nào dính margin hạ xuống dưới 0.05
[*] Giải khung thô (raw frame) lòi ra: aaaaaaaaaaaa2dd42b48374354467b36373830383536642d646234322d346366612d386235362d6336323130396438343137637d7a65
[*] Quy chiếu hệ chữ (as ascii)    thành: b'\xaa\xaa\xaa\xaa\xaa\xaa-\xd4+H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}ze'
[*] Tàn dư thừa thãi (leftover)    0 bit vứt đi sau cái byte tròn vành rõ chữ cuối cùng
```

Con số `min margin 0.500` chứng minh một sự thống trị áp đảo tuyệt đối: không có bất kỳ khoang (slot) nào mà bị hai phe tone đánh lộn giành giật, nên ta chẳng phải đoán mò (guess) số phận của bất kỳ bit nào.

### Bước 3: Đạp đổ 3 phe phân cực bit giả

Thế trận có 4 khả năng nạp bit (ghép chéo: dải tone cao/thấp gán làm 1, đi kèm thứ tự nạp MSB/LSB). Tuy nhiên chỉ có một cấu hình duy nhất tạo ra hình thù văn bản có não:

```text
Phe t85=1 nạp MSB   : Lòi ra chữ in được (printable) 46/54  -> Đích là b'\xaa\xaa...H7CTF{6780856d-db42-...'
Phe t85=1 nạp LSB   : Chữ in được 25/54  -> Rác rưởi
Phe t35=1 nạp MSB   : Chữ in được  7/54  -> Rác rưởi
Phe t35=1 nạp LSB   : Chữ in được 18/54  -> Rác rưởi
```

## Giải phẫu Cấu trúc frame thu được

| Khoang (vùng) | Số hex (byte) | Lời bình phẩm |
| --- | --- | --- |
| Dạo đầu (preamble) | `aa aa aa aa aa aa` | Hình bóng của chuỗi `0b10101010`, dạng chuỗi sóng nhịp điệu luân phiên (alternation) dọn cỗ để đồng bộ nhịp bit (bit sync). |
| Trán khung (header) | `2d d4 2b` | Lai lịch mờ mịt không xác định, có thể là danh xưng thiết bị (device id) kẹp chung với mã nhóm lệnh. |
| Dữ liệu thịt (message) | `48 37 43 54 46 7b … 7d` | Hiện nguyên hình cờ `H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}` (chiếm 43 B) |
| Đuôi (trailer) | `7a 65` | Đoạn này bị câm điếc không thể giải nghĩa: Đem ra đấu `sum8=0x9f`, dập `xor8=0xf7`, thử trò CRC16-CCITT có nhân init 0/FFFF ra = `0xdeea`/`0xd655`, đè CRC16 reflected nhân 0x8005/0xA001 = `0x2d08`/`0x9657`. Tất cả mớ bòng bong đó đều không tài nào nặn ra nổi mã `0x7a65`. Khả năng cao đây chỉ là một cái hằng số nhiễu (nonce) hoặc số thứ tự (serial) rác. |

Lưu ý là bài này không vác cờ đi nộp dạo qua HTTP: Hệ thống máy chủ ngu ngốc này chỉ có vai trò rặn ra duy nhất một con tệp rác tĩnh (`Server: SimpleHTTP/0.6`), hoàn toàn vắng bóng cái cấu trúc hợp đồng điền biểu mẫu nộp đồ `<pre>` như các bài web/hardware anh em khác. Cách duy nhất là bê cái cờ vớt được đem đính trực tiếp lên bảng xếp hạng (scoreboard).

## Flag
```bash
$ python solve_rf.py files/capture.cf32
[+] FLAG: H7CTF{6780856d-db42-4cfa-8b56-c62109d8417c}
```
