# Kick the CAN — Hardware (Medium)

**Flag:** `H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}` · 125 pts · H7TEX 2026
**Target:** `https://web-5c6688f7ad7feac6.web.h7tex.com` · Artifact: `/capture.log` (132 frame candump, 5248 byte)

## Đề bài

Một bản ghi CAN bus lấy từ cổng OBD-II của xe đang vào xưởng. Phần lớn là engine gossip, nhưng có hai
thiết bị nói chuyện riêng với nhau và một bên nói quá nhiều. Việc phải làm: recover thứ mà ECU đã trả ra.

## Phân tích ban đầu

Trang chủ là `Python SimpleHTTP/0.6` chỉ liệt kê một file duy nhất:

```
file: capture.log (SocketCAN candump log: (timestamp) can0 ID#DATA)
Read it with candump/can-utils, Wireshark (SocketCAN), or python-can.
```

Đếm tần suất CAN ID:

```
0C9 158 1A0 1F1 244 2C0 316 3B0   -> mỗi ID hàng chục frame, payload ngắn, vô cấu trúc
7E0                               -> 4 frame
7E8                               -> 8 frame
```

`0x7E0`/`0x7E8` là cặp request/response chuẩn của diagnostic UDS trên nền CAN, chuyên chở bởi ISO-TP
(ISO 15765-2). Tám ID còn lại là traffic định kỳ của động cơ, không có nhịp hỏi-đáp.

## Các hướng đã loại

1. Cờ nằm trong đám traffic powertrain. `0C9 158 1A0 1F1 244 2C0 316 3B0` chiếm gần hết log, payload
   ngắn và vô cấu trúc; chỉ `0x7E0`/`0x7E8` là có cặp request/response.
2. Đọc log bằng `candump`/can-utils/Wireshark/python-can. Host không có công cụ nào trong số đó. Log
   132 dòng nên tự viết bộ reassemble bằng Python chuẩn là nhanh nhất.

## Chuỗi khai thác

**Bước 1 - Gộp lại các thông điệp ISO-TP.** 4 bit đầu của byte đầu tiên là PCI: `0` Single Frame,
`1` First Frame, `2` Consecutive Frame. First Frame cho biết tổng độ dài (`0x102E` → 46 byte), mỗi CF
đóng góp 7 byte.

Chuỗi đáng chú ý nhất, tất cả trên `0x7E8`:

```
7E8#102E62F1A0483743   FF, total = 46
7E8#2154467B36333630   CF 1
7E8#22636262332D3733   CF 2
7E8#2366632D34626135   CF 3
7E8#242D613965362D30   CF 4
7E8#2532323961336231   CF 5
7E8#26613030387D0000   CF 6 (2 byte cuối là padding)
```

Ghép lại được `62 F1 A0` + 43 byte dữ liệu. `62` là positive response của dịch vụ `22`
(ReadDataByIdentifier), `F1A0` là DID. 43 byte còn lại là ASCII thuần:

```
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```

**Bước 2 - Dựng lại toàn bộ phiên chẩn đoán,** để chắc chắn đây là chỗ leak chứ không phải một chuỗi
ASCII tình cờ:

| Hướng | Message | Dịch |
| --- | --- | --- |
| `7E0 →` | `10 03` | DiagnosticSessionControl: bật extended session |
| `← 7E8` | `50 03 0032 01F4` | Positive, P2=50 ms, P2*=5000 ms |
| `7E0 →` | `27 01` | SecurityAccess: xin seed |
| `← 7E8` | `67 01 470C3712` | Positive, seed `47 0C 37 12` |
| `7E0 →` | `27 02 1D566D48` | SecurityAccess: gửi key |
| `← 7E8` | `67 02` | Positive: đã mở khoá |
| `7E0 →` | `22 F1A0` | ReadDataByIdentifier DID 0xF1A0 |
| `← 7E8` | `62 F1A0 <43 byte>` | Flag |

Bên hỏi vào extended session, vượt SecurityAccess bằng cặp seed/key `47 0C 37 12` / `1D566D48`, rồi
mới đọc DID. `0xF1A0` thường là mã phần cứng của ECU; ở đây nó trả về cờ.

**Bước 3 - Chạy lại.** `solve.py` tải log, parse candump, reassemble ISO-TP theo từng CAN ID, tìm UDS
`0x62` và regex `H7CTF\{[^}\n]*\}` trên chính byte đã ghép:

```
python solve.py --url https://web-5c6688f7ad7feac6.web.h7tex.com/capture.log

[*] 132 dòng log -> 132 frame hợp lệ
[*] CAN 0x7E0: 4 thông điệp ISO-TP hoàn chỉnh
[*] CAN 0x7E8: 4 thông điệp ISO-TP hoàn chỉnh

[+] 0x7E8 msg#3: RDBT DID=0xF1A0, 43 byte dữ liệu
    ascii: b'H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}'
```

## Flag
```
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```
