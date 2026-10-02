# Kick the CAN — Hardware (Medium)

**Flag:** `H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}`
**Mục tiêu:** `https://web-5c6688f7ad7feac6.web.h7tex.com` 
**File cung cấp:** `/capture.log` (File log 132 khung tin (frame) candump, dung lượng 5248 byte).

## Đề bài

Hệ thống cung cấp một bản ghi luồng dữ liệu mạng CAN bus được chọc xuất từ cổng OBD-II của một chiếc xe ô tô đang nằm trong xưởng dịch vụ. Phần lớn thông tin trong bản ghi chỉ là những tiếng "lầm bầm" vô nghĩa của động cơ (engine gossip). Nhưng lẫn trong mớ hỗn độn đó, có hai thiết bị (ECU) đang lén lút trò chuyện riêng với nhau, và một bên thì lắm mồm nói hơi nhiều. 
Nhiệm vụ của người chơi là: Phục dựng lại thứ dữ liệu mà khối ECU đó đã phun ra.

## Phân tích ban đầu

Mặt tiền trang chủ khá thô sơ (chạy bằng `Python SimpleHTTP/0.6`), chưng ra một file duy nhất:

```text
file: capture.log (SocketCAN candump log: định dạng (timestamp) can0 ID#DATA)
Gợi ý: Hãy đọc nó bằng công cụ candump/can-utils, Wireshark (chuẩn SocketCAN), hoặc thư viện python-can.
```

Đo tần suất xuất hiện của các mã định danh CAN ID:

```text
Nhóm mã: 0C9, 158, 1A0, 1F1, 244, 2C0, 316, 3B0 -> Mỗi ID này xả ra hàng chục khung tin, payload (dữ liệu thịt) cực ngắn và lộn xộn, vô cấu trúc.
Mã 7E0 -> Xả 4 khung tin.
Mã 7E8 -> Xả 8 khung tin.
```

Bắt bệnh lập tức: Cặp mã `0x7E0` / `0x7E8` chính là bộ mặt kinh điển của giao thức chẩn đoán lỗi xe hơi UDS (Unified Diagnostic Services) hoạt động trên nền mạng CAN. Luồng giao tiếp này được chuyên chở bởi giao thức ISO-TP (ISO 15765-2). Tám mã ID ồn ào còn lại chỉ là nhịp tim định kỳ của khối động cơ, không hề mang tính chất hỏi-đáp.

## Chuỗi khai thác

**Bước 1 - Khâu vá các thông điệp ISO-TP.** 
Theo chuẩn ISO-TP, 4 bit đầu tiên của byte dữ liệu số 0 chính là cờ PCI (Protocol Control Information): 
Cờ `0`: Gói tin đơn (Single Frame), cờ `1`: Gói tin mở màn (First Frame), cờ `2`: Gói tin nối tiếp (Consecutive Frame). 
Gói tin mở màn (First Frame) sẽ gánh luôn trọng trách khai báo tổng độ dài khối thông điệp (ví dụ `0x102E` chỉ định khối dài 46 byte). Mỗi gói Consecutive Frame (CF) theo sau sẽ gùi thêm được 7 byte dữ liệu thịt.

Chuỗi giao tiếp đắt giá nhất, toàn bộ dội về từ mã `0x7E8`:

```text
7E8#102E 62 F1 A0 48 37 43   -> Cờ 1 (First Frame), khai báo độ dài total = 46 byte
7E8#21 54 46 7B 36 33 36 30   -> Cờ 2 (CF 1)
7E8#22 63 62 62 33 2D 37 33   -> Cờ 2 (CF 2)
7E8#23 66 63 2D 34 62 61 35   -> Cờ 2 (CF 3)
7E8#24 2D 61 39 65 36 2D 30   -> Cờ 2 (CF 4)
7E8#25 32 32 39 61 33 62 31   -> Cờ 2 (CF 5)
7E8#26 61 30 30 38 7D 00 00   -> Cờ 2 (CF 6 - 2 byte 00 cuối chỉ là byte đệm lấp chỗ trống padding)
```

Gọt bỏ các mốc cờ PCI và khâu lại, ta thu được chuỗi nguyên thuỷ: `62 F1 A0` nối theo sau là 43 byte dữ liệu. 
Bóc tách: `62` là mã phản hồi chấp thuận (positive response) của dịch vụ `22` (ReadDataByIdentifier - Đọc dữ liệu theo ID). `F1A0` chính là mã định danh dữ liệu (DID). 43 byte đi kèm phía sau là một chuỗi văn bản ASCII thuần khiết:

```text
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```

**Bước 2 - Phục dựng và đối chiếu toàn cảnh phiên chẩn đoán.** 
Để không trở thành kẻ điếc ăn mộng (nhằm đảm bảo đây thực sự là lỗ hổng lấy cờ chứ không phải một chuỗi ASCII tình cờ), ta rọi đèn vào toàn bộ cuộc trò chuyện:

| Chiều | Khung tin (Message) | Lời dịch |
| --- | --- | --- |
| `7E0 →` | `10 03` | Máy quét gửi lệnh (DiagnosticSessionControl): Ép xe nhảy vào phiên chẩn đoán mở rộng (extended session). |
| `← 7E8` | `50 03 0032 01F4` | Xe ngoan ngoãn chấp thuận (Positive), cài đặt hẹn giờ P2=50 ms, P2*=5000 ms. |
| `7E0 →` | `27 01` | Máy quét gửi lệnh (SecurityAccess): "Ê, cho xin hạt giống (seed) bảo mật". |
| `← 7E8` | `67 01 47 0C 37 12` | Xe nhả seed: `47 0C 37 12`. |
| `7E0 →` | `27 02 1D 56 6D 48` | Máy quét giải seed, ném ngược chìa khoá (key): `1D 56 6D 48`. |
| `← 7E8` | `67 02` | Xe báo Positive: "Ổ khoá đã bung". |
| `7E0 →` | `22 F1 A0` | Máy quét ra lệnh: Cho đọc dữ liệu tại DID `0xF1A0`. |
| `← 7E8` | `62 F1 A0 <43 byte>` | Xe ói ra cờ. |

Cuộc hội thoại quá rành mạch: Máy chẩn đoán ép xe vào phiên mở rộng, vượt ải SecurityAccess bằng chiêu giải bài toán seed/key (`47 0C 37 12` / `1D566D48`), sau đó đàng hoàng ra lệnh đọc bộ mã DID. Trong thế giới thực, DID `0xF1A0` thường dùng để cất giữ mã thông số phần cứng của ECU; còn ở cái xưởng xe chết tiệt này, nó nôn ra cờ.

**Bước 3 - Viết công cụ cày tự động.** 
Kịch bản `solve.py` được lập trình để hút thẳng file log, mổ xẻ candump, vá ráp chuẩn xác giao thức ISO-TP theo từng ID, lùng sục mã UDS `0x62` và vớt cờ bằng biểu thức regex `H7CTF\{[^}\n]*\}` ngay trên khối byte thành phẩm:

```bash
python solve.py --url https://web-5c6688f7ad7feac6.web.h7tex.com/capture.log
```

Log thực thi:
```text
[*] Kéo 132 dòng log -> Khớp 132 khung tin hợp lệ
[*] Nhóm CAN 0x7E0: Vá được 4 thông điệp ISO-TP hoàn chỉnh
[*] Nhóm CAN 0x7E8: Vá được 4 thông điệp ISO-TP hoàn chỉnh

[+] Ở dòng CAN 0x7E8 thông điệp số 3: RDBT (Đọc dữ liệu DID) tại mã 0xF1A0, túm được 43 byte dữ liệu
    Dịch ra ASCII: b'H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}'
```

## Flag
```text
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```
