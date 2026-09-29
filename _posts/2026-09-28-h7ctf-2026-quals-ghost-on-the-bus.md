---
title: "Ghost on the Bus — Hardware (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Hardware]
tags: [h7ctf-quals, Hardware]
image:
  path: /CTFWU/H7CTF%202026%20Quals/ghost-on-the-bus/files/de.png
---
**Flag:** `H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}`
**Instance:** `https://web-c2656e4339a3659c.web.h7tex.com`
**Files:** `capture.vcd` (44626 B, 8 kênh logic, timescale 1 ns, 29.79 ms)

## Đề bài

Kẹp logic analyzer vào board "NoiseGate" rồi ghi lại toàn bộ lúc nó boot. Thiết bị đưa provisioning key ra trong routine đánh thức, nhưng "không nói trọn vẹn ở một chỗ nào". Phải tự tìm key từ bản ghi.

## Phân tích ban đầu

Index page cho biết định dạng và danh sách kênh:

```
8-channel logic capture of the device boot (2 MHz). Open in PulseView / sigrok.
Channels: UART_TX, SCL, SDA, SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS, AUX
```

VCD là text nên parse bằng Python thuần, không cần sigrok. Việc đầu tiên là đo nhịp từ histogram khoảng cách transition (`analysis/explore_vcd.py`), vì đề không cho baud ở đâu cả:

```
UART_TX   transitions=1685   gap hist: (8500,1043) (17000,376) (25500,124) ...   -> bit = 8500 ns
SCL       transitions=795    gap hist: (5000,441) (7500,351)                     -> I2C 80 kHz
SDA       transitions=197    gap hist: (12500,92) (25000,28) (37500,21)          -> bội số của SCL
SPI_CLK   transitions=753    gap hist: (1000,751)                                -> 500 kHz, idle low (CPOL=0)
SPI_CS    transitions=3      low 22984000..23738000 ns = 754 us = 376 clock      -> 1 transaction, 47 byte
AUX       transitions=1                                                                -> luôn mức 1, kênh chết
```

8500 ns/bit tức 117650 baud, đúng bằng 2 MHz / 17 mẫu, khớp nhịp logic mà index page công bố.

## Chuỗi khai thác

### Bước 1: UART chính là datasheet

Giải mã `UART_TX` theo khuôn 8N1, phát hiện start bit ở mỗi cạnh xuống rồi đa số theo giữa bit (`level(sym, start + 8500*(1.5+b))`):

```
[boot] NoiseGate bootloader v2.1
[prov] reading key material...
[prov]   part A <- SPI flash READ(0x03) @ 0x001A00, 43 bytes
[prov]   part B <- I2C EEPROM 0x50 (read), 43 bytes
[prov]   provisioning_key = part_A XOR part_B
[prov] key installed. continuing boot.
[boot] done.
```

284 ký tự, 0 ký tự sai stop bit: nếu nhịp bit lệch thì không thể có kết quả sạch như vậy. Log nói rõ phép ghép là XOR và mô tả từng operand bằng đúng giao thức của hai bus còn lại.

### Bước 2: part A từ SPI flash

CS kéo xuống một lần, 376 clock; sample MOSI/MISO ở cạnh lên của CLK (CPOL=0, CPHA=0):

```
MOSI: 03 00 1a 00 ...        <- opcode 0x03 (READ), address 0x001A00, khớp log
MISO: 00 00 00 00 | 75 17 b3 b1 13 b5 6c 39 ... 7b 2b a1
       (4 byte pha lệnh)       43 byte dữ liệu = part A
```

### Bước 3: part B từ I2C EEPROM

START/STOP phát hiện bằng cách SDA đổi trạng thái khi SCL đang giữ mức 1; dữ liệu sample ở cạnh lên của SCL (+300 ns):

```
frame t=23741500  44 bytes: a1 ACK 3d ACK 20 ACK ... 18 ACK dc NACK
slave 0x50 read -> 43 data bytes = part B
```

Byte đầu `0xA1 = 0x50 << 1 | 1` xác nhận đây đúng là pha đọc của EEPROM 0x50 mà log nhắc tới; byte cuối NACK là đúng kịch bản master đọc byte cuối rồi dừng.

### Bước 4: XOR

```python
key = bytes(a ^ b for a, b in zip(part_a, part_b))
```

```
[*] b'H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}'
[+] FLAG: H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}
```

## Flag
```
$ python solve_bus.py files/capture.vcd
[+] FLAG: H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}
```

Ba bằng chứng độc lập rằng phép ghép đúng: cả hai phần đều đúng 43 byte như log tuyên bố; kết quả đúng khuôn `H7CTF{uuid}` với UUID 8-4-4-4-12; và metadata từng bus (opcode `0x03`, address `0x001A00`, slave `0x50` + bit read) đều được log xác nhận trước khi decode.
