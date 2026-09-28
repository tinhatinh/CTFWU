# Notes — Kick the CAN

## Tín hiệu ban đầu

132 frame, phần lớn là "engine gossip": các ID `0C9 158 1A0 1F1 244 2C0 316 3B0` lặp lại với payload ngắn, ngẫu nhiên, không có cấu trúc.

Hai ID khác biệt và chỉ xuất hiện vài lần: **`0x7E0` và `0x7E8`**. Cặp 0x7E0/0x7E8 là diagnostic request/response pair kinh điển trong OBD-II / UDS trên CAN (ISO 15765-2 vận chuyển bằng ISO-TP).

## Reassemble ISO-TP

PCI 4 bit đầu: `0` = Single Frame, `1` = First Frame, `2` = Consecutive Frame.

- `7E0`: 4 thông điệp hoàn chỉnh (toàn bộ là Single Frame).
- `7E8`: 4 thông điệp, trong đó có một chuỗi FF + 6 CF:

```
7E8#102E62F1A0483743   FF, total length = 0x02E = 46 byte
7E8#2154467B36333630   CF#1
7E8#22636262332D3733   CF#2
7E8#2366632D34626135   CF#3
7E8#242D613965362D30   CF#4
7E8#2532323961336231   CF#5
7E8#26613030387D0000   CF#6 (2 byte cuối là padding, bị cắt theo total length)
```

Bỏ 3 byte UDS header `62 F1 A0` còn đúng 43 byte:

```
48374354467b36333630636262332d373366632d346261352d613965362d3032323961336231613030387d
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```

## Hội thoại chẩn đoán đã giải mã

| Hướng | Message | Ý nghĩa |
| --- | --- | --- |
| `7E0 →` | `10 03` | DiagnosticSessionControl, bật extended session |
| `← 7E8` | `50 03 0032 01F4` | Positive: P2=50ms, P2*=5000ms |
| `7E0 →` | `27 01` | SecurityAccess requestSeed |
| `← 7E8` | `67 01 470C3712` | Positive: seed `47 0C 37 12` |
| `7E0 →` | `27 02 1D566D48` | SecurityAccess sendKey |
| `← 7E8` | `67 02` | Positive: đã mở khoá |
| `7E0 →` | `22 F1A0` | ReadDataByIdentifier DID 0xF1A0 |
| `← 7E8` | `62 F1A0 <43 byte>` | Positive: flag bị leak ở đây |

Đúng câu "two boxes were having a far more private conversation. One of them said too much."

## Nhánh đã loại

- Đem `0x7E8#066701470C371200` (Single Frame, PCI 06) ra đọc là `67 01 470C3712` rồi suy đoán WDBT: sai nhãn. `0x67 = 0x27 + 0x40` là reply của **SecurityAccess**, không phải WriteDataByIdentifier. Không ảnh hưởng kết quả.
- Băm payload các ID powertrain (`316`, `0C9`, ...) tìm ASCII: `strings`/regex trên toàn bộ byte không ra mẫu `H7CTF{`. Chỉ có chuỗi `7E0/7E8` là có cấu trúc UDS.
- Không cần `candump`/`python-can`/Wireshark: host không có, và log chỉ 132 dòng nên parser ~40 dòng Python đủ.
