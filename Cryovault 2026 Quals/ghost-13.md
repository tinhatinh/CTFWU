---
title: "GHOST - 13"
category: "Hardware"
tags: ["iot", "ecdsa", "forensics"]
solve_date: "2026-10-11T08:57:00+07:00"
language: "vi"
---

# GHOST - 13

**Flag:** `isfcr{ghost13_dc8f84a256fa64108b6c75a151a1474d}`  
**Artifact:** `plc_firmware.bin` (25,024), `plc_program.bin` (1,600), `plc_traffic.pcap` (5,473), `alarm_buzzer.wav` (93,964), `maintenance_update.ota` (726), `uart_log.txt` (778), `field_service_excerpt.txt` (3,817)

| Artifact | SHA-256 |
|---|---|
| `plc_firmware.bin` | `532395ef38016b0ef29981c7deb6dd3af07abc50af9268ce26a4d04083ae58f7` |
| `plc_program.bin` | `a0a145fe0ec9605ed3a2d9a338f1e66385eed6ac62011a3a9de43b520c8609f0` |
| `plc_traffic.pcap` | `a0de754f697df41db7bc2d3462a6fd9b89db9a763f22123873dfb4e17eab3b59` |
| `alarm_buzzer.wav` | `d9702ffce42d939be89250366cf782eb25b6bf6fa193fa29116ca5c7423bb769` |
| `maintenance_update.ota` | `e084621b293c7c34c51e80fefeffc3dc133bcac29f6db3ac45e58942d34e703d` |
| `uart_log.txt` | `643ce0ac86bfd45c5f2d221e04e2cbe396611618ee0b5055993e1f64514b9d18` |
| `field_service_excerpt.txt` | `6c11b6b0c551480fa44e6a2d3c431923f3e3d9239d0689d72a18f36f0dc99b88` |

## Đề bài

Khôi phục cấu hình PLC đang hoạt động và chuỗi khởi động lại từ firmware, program dump, Modbus capture, buzzer WAV, OTA update, UART log và service manual. Dùng các dữ kiện đó để mở diagnostic secret trong bản cập nhật.

## Phân tích

Manual mô tả các format `G13W`, `G13L`, `G13C`, `G13F`, `G13U` và `G13X`. Firmware có các section `VMBC`, `KDFD`, `PUBK`, `RECV`; CRC của bốn section hợp lệ. Program dump có tám config slot và tám commit journal. Private scalar ECDSA nằm ngoài image, nên không thể lấy trực tiếp từ firmware. UART log ghi một lần brownout giữa hai diagnostic write, gợi ý kiểm tra nonce ECDSA bị dùng lại.

## Lời giải

1. Kiểm tra CRC và commit word của config slot cùng journal. Sequence journal vòng từ 65535 về 0, nên dùng serial arithmetic 16-bit thay vì chọn số lớn nhất. Journal 3 và 4 không hợp lệ. Cấu hình active là slot 5 `TON_WATCHDOG`, sequence 2, epoch 7; lấy ID, salt và `keypad_trim = [9,9,3,2,9,9,9,4]`.
2. Ghép TCP stream theo sequence number trước khi phân tích MBAP. Giữ FC16 `G13C` có CRC16/CCITT-FALSE hợp lệ và đúng địa chỉ register; bỏ retransmission cùng fragment hỏng. Dùng XOR parity phục hồi fragment thiếu của stream 0x41 và 0x42. Ba frame `G13F` dài 118 byte đều có CRC32 đúng.
3. Tính link key bằng SHA-256 của marker `G13/link/v2`, factory constant, ID và salt. Giải mã AES-CTR rồi kiểm tra ba chữ ký ECDSA với `PUBK`. Chỉ ID/salt của slot 5 cho các chữ ký hợp lệ.
4. Stream 0x41 và 0x42 có cùng `r`. Từ `s = k^-1(m+r*d)`, tính `k = (m1-m2)/(s1-s2)` và `d = (s1*k-m1)/r` modulo order của curve. Kiểm tra `d*G == PUBK`; stream 0x43 là đối chứng với nonce khác.
5. Đọc DTMF bằng cửa sổ 25 ms. Các đoạn carrier 440 Hz tách self-check `70372720` khỏi diagnostic code `64658003`. Cộng từng trim modulo 10 thu được `53977997`.
6. Áp dụng sáu hunk `G13X` lên factory image. Target dài 25024 byte, CRC32 `0x922823e4`; kiểm tra SHA-256 prefix theo G13U và CRC của các section. Bản target có KDF constant mới, phải dùng constant này thay factory constant.
7. Dùng HKDF-SHA256 với IKM `d_be32 || ID || salt`; salt là SHA-256 của target constant và committed salt. Info chứa marker diagnostic v4, ID, version little-endian, keypad code và ba digest target/manifest/delta. AES-GCM nonce là ASCII `53977997` nối suffix `ba28ff2e`; AAD là header 60 byte nối raw manifest và delta. Header version 3 và marker không kèm NUL cho tag hợp lệ. Bỏ magic `G13D`, giải nén zlib để đọc flag.

   | jseq | slot | status |
   |---|---|---|
   | 65533…2 | 0…5 | valid, committed |
   | 3 | 6 `TON_WATCHDOG` | journal CRC32 field inconsistent (`0x8eb723c5` stored vs `0x8eb723c4` computed) |
   | 4 | 7 `R_TRIG_ALARM` | commit word `0xffffffff`, never committed; slot CRC32 field also inconsistent |

   ```text
   k = (m1 - m2) / (s1 - s2)   = b467b40088e70a1c81902bcbf6d5bb3b1d571d56bcf58b2b96ef19628c05336a
   d = (s1·k - m1) / r         = 2f1945b86a823a5bffb808c0f5edc9bd981fb15481696d7c29bde45fb8e1a4cb
   d·G == PUBK                 True
   ```

   ```text
   info = "G13/diagnostic/v4" || committed_ID || firmware_version_le16 || keypad_digits_ascii
          || SHA256(target_image) || SHA256(raw_manifest) || SHA256(raw_delta)
   ```

   ```json
   {"diagnostic":"power-restoration","flag":"isfcr{ghost13_dc8f84a256fa64108b6c75a151a1474d}"}
   ```

## Các hướng đã kiểm tra

`RECV` là dữ liệu legacy recovery v1, không phải private scalar của diagnostic v4. Slot 6 và 7 không có commit hợp lệ. Không chia Modbus theo packet boundary vì một request bị chia giữa hai TCP segment. Stream 0x43 không dùng cùng nonce với hai stream dùng để khôi phục scalar.

## Kết quả

Flag được khôi phục offline. ECDSA, public-key reconstruction và GCM tag là các kiểm tra cho từng phần của chuỗi.

`isfcr{ghost13_dc8f84a256fa64108b6c75a151a1474d}`

## Tái hiện

Thực hiện theo chuỗi ở trên: đọc directory và CRC firmware; xác định journal frontier bằng serial arithmetic; ghép TCP/Modbus và phục hồi XOR parity; giải mã CTR và kiểm tra ECDSA; tính scalar; đọc DTMF; áp dụng OTA delta; kiểm tra target; cuối cùng dùng HKDF và GCM để mở sealed record. Các công thức và output trong code block dưới đây giữ nguyên từ bản nguồn. Bài nguồn mô tả thuật toán, không cung cấp một script tổng hợp cho toàn bộ các bước.

```text
FRONTIER (active/committed) -> slot 5 TON_WATCHDOG seq=2 epoch=7
stream 0x41 / 0x42 / 0x43  frame_crc32=OK  sig_verify=OK
NONCE REUSE (r identical for 0x41/0x42)  d*G == PUBK : True
DTMF groups: self-check=70372720  wire=64658003  -> keypad ascii 53977997
target image: ver=3 sections_ok=True crc32=0x922823e4
sealed plaintext magic: b'G13D'
{"diagnostic":"power-restoration","flag":"isfcr{ghost13_dc8f84a256fa64108b6c75a151a1474d}"}
```
