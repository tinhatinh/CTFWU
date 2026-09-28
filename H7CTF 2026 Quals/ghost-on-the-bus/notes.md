# notes.md — Ghost on the Bus (hardware / logic capture)

## H0 — vì sao 404 lúc đầu
evidence: `web-c2650c9b0e3d0251` (tôi gõ sai từ đề) trả `404 page not found` của Go `net/http`, không có header `Server`; host Radio Silence cũng trả y hệt sau khi bị thu route
did: đối chiếu response của host sai vs host đã chết -> kết luận "instance chết" là SAI
result: DEAD — nguyên nhân thật là typo hostname; wildcard DNS của `*.web.h7tex.com` luôn phân giải nên mọi tên sai đều nhận 404 của router. Với `web-c2656e4339a3659c` thì 200 ngay.
bài học: sao chép URL nguyên văn từ message, và một 404 kiểu Go trên subdomain wildcard chưa đủ để khẳng định instance không chạy.

## H1 — định dạng artifact
target: `capture.vcd` 44626 B
evidence: `$timescale 1ns`, 8 `$var wire 1`, kết thúc 29.79 ms -> VCD chuẩn, tự parse được bằng Python, không cần PulseView/sigrok
result: CONFIRMED

## H2 — đo nhịp thay vì đoán
evidence: histogram gap của từng kênh (`analysis/explore_vcd.py`): UART 8500 ns, SCL 12500 ns chu kỳ, SPI_CLK 1000 ns bán kỳ, SPI_CS low đúng 754 µs
did: 8500 ns -> 117650 baud (2 MHz / 17 mẫu); 1 Msps là bẫy: nhịp logic là 2 MHz theo index page
result: CONFIRMED — UART decode ra 284 ký tự in được, **0 ký tự sai stop bit** (chứng chỉ mạnh nhất cho nhịp)

## H3 — UART là "datasheet" giả
evidence: log boot nói thẳng:
```
[prov]   part A <- SPI flash READ(0x03) @ 0x001A00, 43 bytes
[prov]   part B <- I2C EEPROM 0x50 (read), 43 bytes
[prov]   provisioning_key = part_A XOR part_B
```
result: CONFIRMED — "It never says the whole thing in one place" = key nằm ở HAI bus khác nhau và phải XOR

## H4 — SPI
evidence: MOSI = `03 00 1a 00` (opcode READ 0x03, address 0x001A00 -> khớp log), 376 clock -> 47 byte; MISO 4 byte đầu là pha trả lời của opcode/address, 43 byte sau là data
did: sample cả MOSI và MISO ở **rising edge** của CLK (+60 ns guard)
result: CONFIRMED — part A = `7517b3b1…2ba1` đúng 43 byte

## H5 — I2C
evidence: 1 START tại 23741500 ns, 398 SCL rising, gộp 9 bit -> 44 byte: `a1` rồi 43 byte data, byte cuối NACK. `a1 = 0x50<<1|1` khớp "I2C EEPROM 0x50 (read)"
did: phát hiện START/STOP bằng cách SDA đổi trạng thái khi SCL đang ở 1; data bit lấy ở SCL rising +300 ns
result: CONFIRMED — part B = `3d20f0e5…18dc` đúng 43 byte

## Lỗi đã gặp trong lúc decode (không phải lỗi tín hiệu)
1. `sorted(conds + samples)` với tuple `("BIT", t)` / `("START", t)`: so sánh theo **phần tử đầu**, nên mọi bit bị xếp trước mọi condition -> frame rỗng, XOR ra rác. Sửa: đưa mọi thứ về `(time, rank, kind, payload)` để sort theo thời gian.
2. Giá trị khởi tạo ở `#0` (`1!`, `1"`, `1#`...) bị coi là transition thật -> sinh một "STOP" giả và một bit rác trước START. Sửa: bỏ qua event tại t==0.
3. `main()` crash `IndexError` vì lặp qua cả frame 0 byte. Sửa: `if not bs: continue`, và chọn frame theo `slave==0x50 and rw==1` thay vì lấy frame cuối.

## Kết quả
```
part_A (SPI flash @0x001A00, 43 B) XOR part_B (I2C EEPROM 0x50, 43 B)
  = b'H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}'
```
Chạy lại: `python solve_bus.py files/capture.vcd` (in log UART + 2 bus + XOR, tự ghi `flag.txt`)
Kênh AUX không dùng tới (luôn mức 1) — không có mảnh key thứ ba.
