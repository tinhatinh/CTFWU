# Kick the CAN - Hardware (Medium)

**Flag:** `H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}`
**Mục tiêu:** `https://web-5c6688f7ad7feac6.web.h7tex.com` 
**File cung cấp:** `/capture.log` (Bản ghi 132 khung tin candump, kích thước 5248 byte).

## Đề bài

Hệ thống cung cấp tệp tin log mạng CAN bus trích xuất từ cổng OBD-II của một phương tiện. Hầu hết thông tin là tín hiệu nền (engine gossip). Bài toán yêu cầu phân tích dữ liệu, nhận diện hai thiết bị ECU có lưu lượng trao đổi cao và trích xuất dữ liệu đang được truyền tải.

## Phân tích ban đầu

Giao diện hệ thống đơn giản (sử dụng `Python SimpleHTTP/0.6`), cung cấp duy nhất tệp tin:

```text
file: capture.log (SocketCAN candump log: định dạng (timestamp) can0 ID#DATA)
Gợi ý: Hãy đọc nó bằng công cụ candump/can-utils, Wireshark (chuẩn SocketCAN), hoặc thư viện python-can.
```

Phân tích tần suất xuất hiện của các mã CAN ID:

```text
Nhóm mã: 0C9, 158, 1A0, 1F1, 244, 2C0, 316, 3B0 -> Mỗi ID truyền hàng chục khung tin, payload ngắn và không theo cấu trúc cụ thể.
Mã 7E0 -> Có 4 khung tin.
Mã 7E8 -> Có 8 khung tin.
```

Nhận diện cấu trúc: Các mã `0x7E0` / `0x7E8` là dấu hiệu đặc trưng của giao thức chẩn đoán UDS (Unified Diagnostic Services) trên nền CAN bus. Giao thức này sử dụng chuẩn truyền tải ISO-TP (ISO 15765-2). Các mã ID khác đóng vai trò chu kỳ định kỳ của động cơ, không chứa giao tiếp hỏi-đáp.

## Quá trình khai thác

**Bước 1 - Kết hợp các thông điệp ISO-TP.** 
Theo chuẩn ISO-TP, 4 bit đầu của byte dữ liệu số 0 biểu thị cờ PCI (Protocol Control Information): 
Cờ `0`: Gói tin đơn (Single Frame), cờ `1`: Gói tin mở màn (First Frame), cờ `2`: Gói tin nối tiếp (Consecutive Frame). 
Gói tin mở màn (First Frame) xác định tổng độ dài khối thông điệp (ví dụ `0x102E` chỉ định độ dài 46 byte). Mỗi Consecutive Frame (CF) theo sau sẽ mang thêm 7 byte dữ liệu.

Chuỗi giao tiếp quan trọng nhất được ghi nhận từ mã `0x7E8`:

```text
7E8#102E 62 F1 A0 48 37 43   -> Cờ 1 (First Frame), tổng độ dài = 46 byte
7E8#21 54 46 7B 36 33 36 30   -> Cờ 2 (CF 1)
7E8#22 63 62 62 33 2D 37 33   -> Cờ 2 (CF 2)
7E8#23 66 63 2D 34 62 61 35   -> Cờ 2 (CF 3)
7E8#24 2D 61 39 65 36 2D 30   -> Cờ 2 (CF 4)
7E8#25 32 32 39 61 33 62 31   -> Cờ 2 (CF 5)
7E8#26 61 30 30 38 7D 00 00   -> Cờ 2 (CF 6 - 2 byte 00 cuối là dữ liệu padding)
```

Sau khi loại bỏ các byte điều khiển PCI và ghép các khung dữ liệu, chuỗi thông điệp hoàn chỉnh là: `62 F1 A0` nối theo sau là 43 byte dữ liệu. 
Phân tích: `62` là mã phản hồi xác nhận (positive response) của dịch vụ `22` (ReadDataByIdentifier). `F1A0` là mã định danh dữ liệu (DID). 43 byte đính kèm phía sau tương ứng văn bản định dạng ASCII:

```text
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```

**Bước 2 - Phân tích đối chiếu luồng chẩn đoán.** 
Để xác nhận tính nhất quán của luồng dữ liệu, quá trình giao tiếp được phân tích chi tiết:

| Chiều | Khung tin (Message) | Lời dịch |
| --- | --- | --- |
| `7E0 →` | `10 03` | Lệnh DiagnosticSessionControl: Chuyển ECU sang phiên chẩn đoán mở rộng (extended session). |
| `← 7E8` | `50 03 0032 01F4` | Phản hồi xác nhận (Positive), thông số hẹn giờ P2=50 ms, P2*=5000 ms. |
| `7E0 →` | `27 01` | Lệnh SecurityAccess: Yêu cầu cấp seed bảo mật. |
| `← 7E8` | `67 01 47 0C 37 12` | Phản hồi cung cấp seed: `47 0C 37 12`. |
| `7E0 →` | `27 02 1D 56 6D 48` | Gửi mã khóa bảo mật (key): `1D 56 6D 48`. |
| `← 7E8` | `67 02` | Xác thực thành công (Positive). |
| `7E0 →` | `22 F1 A0` | Yêu cầu đọc dữ liệu tại DID `0xF1A0`. |
| `← 7E8` | `62 F1 A0 <43 byte>` | Trả về thông tin chứa mã cờ. |

Luồng giao tiếp diễn ra chuẩn xác: Thiết bị kiểm tra khởi chạy phiên mở rộng, vượt qua xác thực SecurityAccess (cặp seed/key `47 0C 37 12` / `1D566D48`), và truy xuất cấu hình thiết bị. Trên thực tế, DID `0xF1A0` thường dùng lưu mã định danh phần cứng; trong môi trường thử thách, DID này trả về mã cờ.

**Bước 3 - Tự động hóa quá trình phân tích.** 
Kịch bản `solve.py` được thiết kế để đọc tệp log, nhận diện cấu trúc ISO-TP, lọc các mã dịch vụ `0x62` và áp dụng biểu thức chính quy `H7CTF\{[^}\n]*\}` để xuất cờ:

```bash
python solve.py --url https://web-5c6688f7ad7feac6.web.h7tex.com/capture.log
```

Log thực thi:
```text
[*] Kéo 132 dòng log -> Khớp 132 khung tin hợp lệ
[*] Nhóm CAN 0x7E0: Vá được 4 thông điệp ISO-TP hoàn chỉnh
[*] Nhóm CAN 0x7E8: Vá được 4 thông điệp ISO-TP hoàn chỉnh

[+] Ở dòng CAN 0x7E8 thông điệp số 3: RDBT (Đọc dữ liệu DID) tại mã 0xF1A0, thu được 43 byte dữ liệu
    Dịch ra ASCII: b'H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}'
```

## Flag
```text
H7CTF{6360cbb3-73fc-4ba5-a9e6-0229a3b1a008}
```
