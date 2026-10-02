# Open Sesame — Hardware (Hard)

**Flag:** `H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}` (Máy chủ nhả qua cổng `/unlock`, đã cất vào hộp `flag.txt`)
**Mục tiêu:** `https://web-7a56034b5423964c.web.h7tex.com` 
**Đồ nghề (Artifact):** `capture.cf32` (Luồng dữ liệu băng gốc baseband định dạng I/Q float32 little-endian, tốc độ mẫu 1 MHz)

## Đề bài

Trò chơi đưa ta một chiếc remote gara cửa cuốn hàng bình dân. Điểm quái gở của nó là mỗi lần bấm, nó lại khạc ra một dải mã hoàn toàn mới. Đề bài tử tế cấp cho ta bản ghi băng gốc (baseband) thô của đúng 8 lần bấm phím liên tiếp. Kèm theo đó là một câu mỉa mai chí mạng: "Cái không đoán lụi được (unguessable) không có nghĩa là cái không tính trước được (unpredictable)". 
Nhiệm vụ của người chơi: Tính toán chính xác dải mã mà chiếc remote chết tiệt này sẽ phát ra ở cú bấm phím thứ 9, và nộp nó cho hệ thống để mở cửa.

## Phân tích ban đầu

Mổ xẻ file `capture.cf32`: Đây là một luồng dữ liệu I/Q dạng số thực float32, kiến trúc little-endian (LE) được nén ở tốc độ lấy mẫu 1 MHz. Do hệ thống máy trạm (host) của ta nghèo nàn, không được trang bị GNU Radio cũng chẳng có đồ nghề urh, nên phải xắn tay áo lên mà tự giải mã điều chế (demodulate) bằng phương pháp thủ công.

## Chuỗi khai thác

**Bước 1 - Lột trần đường bao biên độ (Envelope).** 
Sử dụng công thức kinh điển `env = I^2 + Q^2` để lấy đường bao. Tuy nhiên tín hiệu thô có rất nhiều răng cưa (ripple), buộc ta phải mài phẳng nó bằng cách chạy một bộ lọc làm mượt (smoothing) với cửa sổ rộng 20 micro-giây cho mỗi chip (chu kỳ bit cơ sở).

**Bước 2 - Thiết lập ranh giới OOK.** 
Tính toán ngưỡng cắt âm bằng công thức `p1 + 0.35*(max - p1)`. Cắt tín hiệu qua ngưỡng này, ta thu gom được tổng cộng 392 khối phát sóng nhỏ (burst).

**Bước 3 - Cắt khúc từng lần bấm.** 
Rà soát thời gian im lặng, nếu thấy khe hở nào dài hơn 1.5 mili-giây thì chém xuống làm mốc chia tách. Lát chém này chia dải sóng ra thành chính xác 8 lần bấm phím riêng biệt (được ngăn cách bởi 7 khe hở tĩnh lặng siêu dài, mỗi khe kéo dài cỡ ~10 chu kỳ T).

**Bước 4 - Mổ xẻ chuỗi bit trong một lần bấm.** 
Cấu trúc độ dài mạch chạy (run-length) rất nguyên thủy, chỉ tuân theo hai khổ độ: 1T và 2T (với mỗi T dài 303 micro-giây). Mỗi cụm bấm nén 97 vạch chạy (run), tương đương với công thức `1 + 2×48` -> Suy ra có tròn 48 bit dữ liệu. Mỗi bit được biểu diễn theo một cặp trạng thái (High, Low): Cấu trúc `H1L2` tương ứng bit 0, còn cấu trúc `H2L1` tương ứng bit 1.

**Bước 5 - Bộ sưu tập 8 khung sóng (Frame).**
Giải mã toàn bộ, ta moi ra được 8 dải mã hex tĩnh:

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

**Bước 6 - Giải phẫu mô hình mã lặp (Rolling code).** 
Băm cái dải 48 bit (12 ký tự hex) ra thành ba khúc ruột: `32 bit cứng (cố định) | 12 bit bộ đếm (counter) | 4 bit đuôi kiểm định checksum (crc)`:

| Lần bấm | Bộ đếm (counter) | Nibble đuôi (crc) | Tổng toán học của 11 nibble đầu (rồi chia lấy dư mod 16) |
| --- | --- | --- | --- |
| 0 | 0xbe1 | 3 | 3 |
| 1 | 0xc11 | 7 | 7 |
| 2 | 0xc41 | a | a |
| 3 | 0xc71 | d | d |
| 4 | 0xca1 | 0 | 0 |
| 5 | 0xcd1 | 3 | 3 |
| 6 | 0xd01 | 7 | 7 |
| 7 | 0xd31 | a | a |

Quy luật phơi bày trần trụi:
- Khối đếm counter tăng vùn vụt một cách cơ học `+0x30` sau mỗi nhát bấm, bất di bất dịch qua cả 8 nhịp.
- Thuật toán crc thô sơ đến thảm thương: `crc = (tổng giá trị của 11 cụm 4 bit (nibble) đầu tiên) theo modulo 16`. Công thức này ráp khít khịt với cả 8 khung.

Hoá ra cái trò "mã mới mỗi lần bấm" chỉ là một cú lừa: mã đổi là do cái biến counter nhảy số. Câu sấm truyền "unguessable ≠ unpredictable" của tác giả cắm phập vào đúng huyệt đạo này. Toàn bộ cỗ máy sinh mã chỉ là sự chắp vá giữa một cái counter thô thiển lố bịch và một mã kiểm tra CRC đúc từ phép cộng cấp một.

**Bước 7 - Bói ra lần bấm thứ 9.**
Chỉ việc vác máy tính ra cộng:

```text
Bước counter = 0xd31 + 0x30 = 0xd61
Khung thân    = 4f122809 d61  + crc
Toán crc      = (4+15+1+2+2+8+0+9 + 13+6+1) mod 16 = 61 mod 16 = 13 = d (hệ hex)
Dải mã cuối   = 4f122809d61d
```

**Bước 8 - Lời bào chữa (Kiểm chứng tính đúng).** 
Hai quy luật bất tử ở trên được rèn qua ngọn lửa của TẤT CẢ 8 khung mã thu được, chứ không phải dựa trên sự ăn may từ một khung: Đoạn 32 bit mào đầu cứng như đá, giống đúc nhau ở mọi khung; và khoảng cách counter (hiệu số) giữa hai lần bấm sát vách luôn bị khóa cứng ở `0x30`. Đem công thức CRC đè lên bất kỳ khung nào, nó cũng khạc ra kết quả khớp boong với nibble chốt đuôi.

## Flag
```bash
python solve.py https://web-7a56034b5423964c.web.h7tex.com analysis/capture.cf32 --submit
```

Cửa gara nhả cờ:
```text
[*] Gõ cửa /unlock -> Nhận mã 200 OK
{"status": "unlocked", "flag": "H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}"}
```
