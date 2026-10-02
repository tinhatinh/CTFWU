# Ghost on the Bus — Hardware (Medium)

**Flag:** `H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}`
**Dịch vụ mạng:** `https://web-c2656e4339a3659c.web.h7tex.com`
**Files cung cấp:** `capture.vcd` (File dump 44.626 B, ghi nhận 8 kênh logic, tần số mẫu 1 ns, kéo dài 29.79 ms).

## Đề bài

Hệ thống cung cấp kết quả phân tích logic (logic analyzer) của bảng mạch "NoiseGate" trong quá trình khởi động (boot). Thông số cho biết thiết bị cung cấp khoá cấu hình (provisioning key) trong quá trình này, tuy nhiên không trả về toàn bộ mã tại một vị trí duy nhất. Yêu cầu của bài toán là phân tích tín hiệu điện để tổng hợp lại mã khóa hệ thống.

## Phân tích ban đầu

Đánh giá tài liệu định dạng (Index page), hệ thống sử dụng định dạng file VCD với sơ đồ (pinout) của 8 kênh logic:

```text
Bản ghi logic 8 kênh của quá trình boot thiết bị (Tần số lấy mẫu 2 MHz). Mở bằng PulseView / sigrok.
Các kênh: UART_TX, SCL, SDA, SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS, AUX
```

File VCD sử dụng định dạng văn bản (text), do đó có thể xử lý và phân tích tự động bằng ngôn ngữ Python thay vì chỉ thao tác bằng `sigrok`. 
Dữ liệu tốc độ truyền (baud rate) không được cung cấp. Phân tích tốc độ tín hiệu qua biểu đồ tần suất (histogram) các khoảng thời gian chuyển đổi mạch (transition) bằng kịch bản `analysis/explore_vcd.py`:

```text
Kênh UART_TX   Ghi nhận 1685 pha chuyển mạch   Gap hist: (8500,1043) (17000,376) (25500,124) ...   -> Đo tốc độ bit = 8500 ns
Kênh SCL       Ghi nhận 795 pha chuyển mạch    Gap hist: (5000,441) (7500,351)                     -> Chuẩn I2C 80 kHz
Kênh SDA       Ghi nhận 197 pha chuyển mạch    Gap hist: (12500,92) (25000,28) (37500,21)          -> Tần số đồng bộ với SCL
Kênh SPI_CLK   Ghi nhận 753 pha chuyển mạch    Gap hist: (1000,751)                                -> Giao tiếp SPI 500 kHz, cấu hình (CPOL=0)
Kênh SPI_CS    Ghi nhận 3 pha chuyển mạch      Kéo xuống thấp 22.984.000..23.738.000 ns = 754 us = 376 chu kỳ xung nhịp -> Đo đạc 1 luồng truyền 47 byte
Kênh AUX       Ghi nhận 1 pha chuyển mạch                                                          -> Tín hiệu không hoạt động
```

Chu kỳ 8500 ns/bit tương đương với tốc độ 117.650 baud, phù hợp với tần số lấy mẫu 2 MHz / 17 mẫu, đúng với thông số khởi tạo 2 MHz của hệ thống.

## Quá trình khai thác

### Bước 1: Trích xuất thông tin cấu hình từ luồng UART

Tiến hành phân tích kênh `UART_TX` với cấu hình 8N1 (1 bit bắt đầu, 8 bit dữ liệu, không chẵn lẻ, 1 bit kết thúc). Quy luật phân tích: bit bắt đầu (start bit) định vị tại sườn âm (cạnh xuống), dữ liệu được đọc tại điểm giữa mỗi chu kỳ (`level(sym, start + 8500*(1.5+b))`). Chuỗi log hệ thống hiển thị:

```text
[boot] NoiseGate bootloader v2.1
[prov] reading key material...
[prov]   part A <- SPI flash READ(0x03) @ 0x001A00, 43 bytes
[prov]   part B <- I2C EEPROM 0x50 (read), 43 bytes
[prov]   provisioning_key = part_A XOR part_B
[prov] key installed. continuing boot.
[boot] done.
```

Đoạn log thu nhận 284 ký tự chính xác, không phát hiện lỗi tại các stop bit, xác minh thuật toán định vị tốc độ truyền. Quan trọng hơn, dữ liệu này chỉ ra thuật toán để giải mã khóa cấu hình (provisioning key): kết hợp hai phần (part A và part B) được lấy từ SPI và I2C bằng phép toán XOR.

### Bước 2: Trích xuất phần "part A" từ SPI Flash

Trên kênh SPI, tín hiệu CS (Chip Select) kích hoạt mức thấp trong thời gian 376 chu kỳ xung nhịp (clock). Lấy mẫu các dữ liệu MOSI/MISO tại sườn dương của xung CLK (cấu hình CPOL=0, CPHA=0):

```text
MOSI (Lệnh truyền): 03 00 1a 00 ...        <- Opcode 0x03 (READ), địa chỉ 0x001A00 (đồng bộ với dữ liệu từ UART).
MISO (Đọc về):      00 00 00 00 | 75 17 b3 b1 13 b5 6c 39 ... 7b 2b a1
                    (4 byte tín hiệu định tuyến) | 43 byte dữ liệu chính = part A
```

### Bước 3: Trích xuất phần "part B" từ I2C EEPROM

Đối với luồng I2C, cờ START và STOP được xác nhận qua sự thay đổi trạng thái chân dữ liệu SDA trong khi chân SCL duy trì ở mức cao (mức 1). Dữ liệu được thu nhận tại sườn dương của SCL (độ trễ ước tính +300 ns):

```text
Khung hình bắt đầu lúc t=23.741.500ns ghi nhận 44 byte: a1 (ACK) 3d (ACK) 20 (ACK) ... 18 (ACK) dc (NACK)
Trạng thái: Địa chỉ thiết bị 0x50 phản hồi -> Trả về 43 byte dữ liệu chính = part B
```

Kiểm tra thông số: Byte ban đầu `0xA1` là `(0x50 << 1) | 1` - khớp với mã đọc (read) thiết bị `0x50` từ EEPROM theo hướng dẫn UART. Bit kết thúc là NACK đúng chuẩn điều khiển cho ngắt truyền sau byte cuối.

### Bước 4: Kết hợp dữ liệu (XOR)

```python
# Thực hiện thuật toán kết hợp
key = bytes(a ^ b for a, b in zip(part_a, part_b))
```

```text
Kết quả thu được:
[*] b'H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}'
[+] FLAG: H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}
```

## Flag
```bash
$ python solve_bus.py files/capture.vcd
[+] FLAG: H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}
```

Có ba cơ sở độc lập xác thực tính chính xác của phương pháp giải: Dữ liệu hai mảng A và B cung cấp chuẩn 43 byte theo yêu cầu; kết quả cuối theo định dạng cờ `H7CTF{uuid}` (chuẩn UUID 8-4-4-4-12); và các siêu dữ liệu cấu hình kênh truyền (như opcode `0x03`, địa chỉ `0x001A00`, slave `0x50` cùng bit read) đều đồng bộ dữ liệu trích xuất từ luồng UART.
