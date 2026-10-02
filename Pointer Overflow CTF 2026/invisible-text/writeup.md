# Invisible Text — STEG (200 pts)

**Flag:** `POCTF{PIEMPAOSMHDLEGRT}`
**Files:** `invisible_text.py` (4245 B, sha256 `f027442b37a521f4a775ec56d37336df446d83e7acd641042e28af030f745320`)

## Đề bài

Tác giả gợi ý rằng có một thông điệp được cất giấu bên trong tệp tin, và yêu cầu người chơi phân tích kỹ lưỡng. Thử thách cung cấp tệp mã nguồn `invisible_text.py` (tệp được sinh riêng cho từng đội, ví dụ: `invisible_text_612.py`). Nhiệm vụ là trích xuất thông điệp ẩn bên trong mã nguồn và nộp. Thử thách không yêu cầu giao tiếp với dịch vụ từ xa.

## Phân tích ban đầu

Tệp tin là mã Python, kích thước 4245 byte, bao gồm 81 dòng văn bản định dạng UTF-8. Phân tích nội dung cho thấy tệp chỉ chứa một ký tự ngoài dải ASCII chuẩn là dấu gạch ngang `—` trong phần bình luận (comment). Không ghi nhận các kỹ thuật giấu tin như Zero Width Space, BOM (Byte Order Mark), NBSP, hoặc ký tự đồng dạng (homoglyph).

Chi tiết đáng chú ý là **47 trên tổng số 81 dòng mã kết thúc bằng các khoảng trắng (whitespace) dư thừa**. Cụ thể:

```text
dòng 1   SSSTSTSSSS        (chứa 10 ký tự khoảng trắng/tab)
dòng 2   T                 (chứa đúng 1 ký tự tab)
dòng 3   SSSSSTSSTTTT      (chứa 12 ký tự)
dòng 4   T
dòng 5   SSSSSTSSSSTT
...
dòng 45  SSSSSTTTTTST
dòng 46  T
dòng 47  SS                (chứa 2 ký tự)
```
*(Quy ước: `S` là Space, `T` là Tab).*

Các dòng lẻ có độ dài cố định là 12 ký tự (ngoại trừ dòng đầu tiên có 10 ký tự), trong khi các dòng chẵn chứa một ký tự tab. Dữ liệu ẩn nằm trong các khoảng trắng cuối dòng này.

Mã nguồn bề mặt là một công cụ `diary_reader.py`, thực hiện nối 46 khối base64, giải mã bằng `b64decode`, bung nén với `zlib.decompress`, và in kết quả. Khi thực thi (yêu cầu ghi kết quả ra tệp UTF-8 để tránh lỗi `UnicodeEncodeError` trên môi trường Windows cp1252), đầu ra là 2145 ký tự braille (chữ nổi) trên 33 dòng. Đây là dữ liệu đánh lạc hướng (decoy).

## Quá trình phân tích

**Bước 1 — Phân tích mẫu dữ liệu (Fixed-length groups).** 
Các dòng lẻ chứa 12 ký tự khoảng trắng, trong đó vị trí thứ sáu **luôn là một dấu tab**. Đây là mô hình mã hoá 7-bit: 5 ký tự space đầu tiên đóng vai trò đệm (padding) căn lề, và 7 ký tự cuối mang dữ liệu.

**Bước 2 — Trích xuất dữ liệu, quy ước `tab = 1`, `space = 0`.** 
Ký tự ASCII in được có bit cao nhất (MSB) bằng 1. Việc nhóm 7 bit luôn bắt đầu bằng tab (tương đương bit 1) hỗ trợ xác định ranh giới bit.

```python
flag = ""
for line in src.split("\n"):
    tail = line[len(line.rstrip()):]
    if len(tail) < 7:
        continue
    bits = tail[-7:].replace(" ", "0").replace("\t", "1")
    flag += chr(int(bits, 2))
```

Thực thi đoạn mã trên trả về kết quả:

```text
  dòng   1  TSTSSSS  =  80  'P'
  dòng   3  TSSTTTT  =  79  'O'
  dòng   5  TSSSSTT  =  67  'C'
  dòng   7  TSTSTSS  =  84  'T'
  dòng   9  TSSSTTS  =  70  'F'
  dòng  11  TTTTSTT  = 123  '{'
  ...
  dòng  45  TTTTTST  = 125  '}'
MESSAGE: POCTF{PIEMPAOSMHDLEGRT}
```

**Bước 3 — Đánh giá kết quả.** 
Phương pháp được xác nhận qua ba yếu tố:
(a) 22/22 nhóm 12 ký tự đều có tab tại vị trí thứ sáu.
(b) Tổng số dòng chứa thông điệp là 23, tương đương độ dài cờ: `POCTF{` (6 ký tự) + thân cờ (16 ký tự) + `}` (1 ký tự).
(c) Chuỗi ký tự khớp với định dạng cờ tiêu chuẩn của hệ thống.
Các dấu cách ở phần đầu dòng (padding) không chứa thông tin.

**Bước 4 — Xác thực cờ.**

```http
POST /challenges/invisible-text/submit
{"flag":"POCTF{PIEMPAOSMHDLEGRT}"}
```

Hệ thống phản hồi:
```json
HTTP 200 :: {"correct":true,"message":"Correct."}
```

## Flag

```
POCTF{PIEMPAOSMHDLEGRT}
```

Thông điệp bí mật được lưu trữ tại vùng **khoảng trắng cuối dòng** của tệp mã nguồn. Các lớp mã hóa cơ bản (base64, zlib, braille) chỉ có chức năng làm nhiễu thông tin.

## Reproduce

```bash
python exploit.py files/invisible_text.py
```
