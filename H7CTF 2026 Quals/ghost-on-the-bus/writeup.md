# Ghost on the Bus — Hardware (Medium)

**Flag:** `H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}`
**Dịch vụ mạng:** `https://web-c2656e4339a3659c.web.h7tex.com`
**Files cung cấp:** `capture.vcd` (File dump 44.626 B, thu thập 8 kênh logic, tần số mẫu 1 ns, kéo dài 29.79 ms).

## Đề bài

Vở kịch mở ra khi ta kẹp thiết bị phân tích logic (logic analyzer) vào bảng mạch "NoiseGate" và ghi hình toàn bộ quá trình mạch khởi động (boot). Nhà sản xuất tuyên bố: thiết bị này sẽ nôn ra khoá cấu hình (provisioning key) trong quá trình đánh thức, nhưng quái oăm ở chỗ "nó không chịu phun ra toàn bộ ở cùng một chỗ". Thử thách yêu cầu người chơi phải tự mò mẫm, nội suy và lắp ráp lại chiếc chìa khoá từ mớ hỗn độn của tín hiệu điện.

## Phân tích ban đầu

Đọc lướt qua trang chủ (Index page), ta thu lượm được định dạng file và sơ đồ chân (pinout) của 8 kênh logic:

```text
Bản ghi logic 8 kênh của quá trình boot thiết bị (Tần số lấy mẫu 2 MHz). Mở bằng PulseView / sigrok.
Các kênh: UART_TX, SCL, SDA, SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS, AUX
```

Khác với các định dạng nhị phân, file VCD thực chất là văn bản thuần (text). Thế nên, thay vì dùng `sigrok`, ta hoàn toàn có thể tự viết mã Python để mổ bụng nó một cách nhẹ nhàng. 
Bởi vì đề bài cố tình giấu nhẹm tốc độ truyền (baud rate), việc sống còn đầu tiên là phải tự đo nhịp tim của luồng dữ liệu bằng cách phân tích biểu đồ tần suất (histogram) các khoảng cách chuyển mạch (transition) bằng công cụ tự chế `analysis/explore_vcd.py`:

```text
Kênh UART_TX   Đếm 1685 pha chuyển mạch   Gap hist: (8500,1043) (17000,376) (25500,124) ...   -> Chốt tốc độ bit = 8500 ns
Kênh SCL       Đếm 795 pha chuyển mạch    Gap hist: (5000,441) (7500,351)                     -> Chuẩn giao tiếp I2C 80 kHz
Kênh SDA       Đếm 197 pha chuyển mạch    Gap hist: (12500,92) (25000,28) (37500,21)          -> Chạy theo bội số của SCL
Kênh SPI_CLK   Đếm 753 pha chuyển mạch    Gap hist: (1000,751)                                -> Giao tiếp SPI 500 kHz, mức idle thấp (CPOL=0)
Kênh SPI_CS    Đếm 3 pha chuyển mạch      Chìm ở mức thấp 22.984.000..23.738.000 ns = 754 us = 376 chu kỳ clock -> Ghi nhận 1 đợt truyền, dài 47 byte
Kênh AUX       Đếm 1 pha chuyển mạch                                                          -> Luôn kẹt ở mức 1, kênh chết lâm sàng
```

Phép tính 8500 ns/bit giải mã ra chuẩn 117.650 baud, cực kỳ vừa vặn với tỷ lệ 2 MHz / 17 mẫu. Con số này ăn khớp hoàn hảo với nhịp xung logic 2 MHz mà trang chủ đã úp mở.

## Chuỗi khai thác

### Bước 1: Khai thác UART như một cuốn cẩm nang (Datasheet)

Khi bẻ khoá luồng `UART_TX` bằng cấu hình chuẩn 8N1 (1 bit bắt đầu, 8 bit dữ liệu, không chẵn lẻ, 1 bit kết thúc). Quy luật: bit bắt đầu (start bit) luôn nằm ở sườn âm (cạnh xuống), đa số các bit dữ liệu được chốt hạ ở chính giữa chu kỳ (`level(sym, start + 8500*(1.5+b))`). Chuỗi log hiện hình:

```text
[boot] NoiseGate bootloader v2.1
[prov] reading key material...
[prov]   part A <- SPI flash READ(0x03) @ 0x001A00, 43 bytes
[prov]   part B <- I2C EEPROM 0x50 (read), 43 bytes
[prov]   provisioning_key = part_A XOR part_B
[prov] key installed. continuing boot.
[boot] done.
```

Đoạn log thu về sạch bong, tròn trịa 284 ký tự mà không hề vấp phải một lỗi sai bit kết thúc (stop bit) nào. Điều này khẳng định thuật toán đo nhịp bit đã chuẩn xác tuyệt đối. Đắt giá hơn, đoạn log này đóng vai trò như một bản thiết kế phơi bày thuật toán giải mã: chìa khoá cuối cùng là phép nội suy XOR, với hai thành tố được bốc ra từ chính hai đường bus SPI và I2C còn lại.

### Bước 2: Truy xuất mảnh "part A" từ bộ nhớ SPI Flash

Trên kênh SPI, chân CS (Chip Select) bị kéo xuống đáy duy nhất một lần, chìm trong suốt 376 chu kỳ xung nhịp (clock). Lấy mẫu (sample) các đường MOSI/MISO ở sườn dương của xung CLK (cấu hình chuẩn CPOL=0, CPHA=0):

```text
MOSI (Lệnh gọi): 03 00 1a 00 ...        <- Mã lệnh 0x03 (READ), vạch mặt địa chỉ 0x001A00, khớp 100% với log.
MISO (Đổ về):    00 00 00 00 | 75 17 b3 b1 13 b5 6c 39 ... 7b 2b a1
                  (4 byte rác của pha lệnh) | 43 byte dữ liệu thịt = part A
```

### Bước 3: Truy xuất mảnh "part B" từ I2C EEPROM

Trên I2C, cờ START và STOP được định vị bằng thao tác lật trạng thái chân dữ liệu SDA trong khi chân đồng hồ SCL vẫn đang neo ở mức cao (mức 1). Dữ liệu được vớt ở sườn dương của SCL (trễ tĩnh +300 ns):

```text
Khung hình bắt đầu lúc t=23.741.500ns chứa 44 byte: a1 (ACK) 3d (ACK) 20 (ACK) ... 18 (ACK) dc (NACK)
Trạng thái: Thiết bị tớ (slave) ở địa chỉ 0x50 phản hồi -> Nhả 43 byte dữ liệu thịt = part B
```

Kiểm tra đối chiếu: Byte khởi điểm `0xA1` thực chất bằng `(0x50 << 1) | 1` - mã hiệu nhận dạng chính xác pha đọc (read) của EEPROM `0x50` mà luồng UART đã chỉ điểm. Kết thúc bằng một bit NACK là hoàn toàn đúng kịch bản thiết bị chủ (master) chủ động cắt đứt kết nối sau khi đọc xong byte cuối cùng.

### Bước 4: Chốt hạ bằng XOR

```python
# Kịch bản ghép mảnh bằng toán học
key = bytes(a ^ b for a, b in zip(part_a, part_b))
```

```text
Kết quả:
[*] b'H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}'
[+] FLAG: H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}
```

## Flag
```bash
$ python solve_bus.py files/capture.vcd
[+] FLAG: H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}
```

Có tận 3 lời khai độc lập bảo chứng cho tính đúng đắn của chuỗi giải mã này: Cả hai mảnh A và B đều nặn ra chuẩn 43 byte như log dự báo; chuỗi kết quả có khuôn mẫu chuẩn xác `H7CTF{uuid}` (với UUID định dạng 8-4-4-4-12); và toàn bộ các thông số meta của mỗi dòng bus (như opcode `0x03`, địa chỉ `0x001A00`, slave `0x50` + bit read) đều đã được tiên tri và phê duyệt bởi kênh log trước khi bung nén.
