---
title: "Invisible Scan"
category: "Misc"
tags: ["ascii-art", "qr-code", "unicode-steganography", "zero-width", "bitstream"]
solve_date: "2026-10-10T17:29:00+07:00"
language: "vi"
points: 159
---

# Invisible Scan

**Flag:** `kBxAc{a5(Ii_AR7_MasTER_caNv@$_h1DdEn_In_the_piXelS_oF_THE_(ODE}`  
**Tác giả:** HydraRoot  
**File đề:** `invisiblescan.zip`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `invisiblescan.zip` | 1,838 | `8285314728704719d663a5b98a72a7ec44f107bdb758721607db4e19ff36c736` |
| `challenge.bin` | 15,931 | `b8d275156462e6dede12f001a049e3da14ba8b1bd5d7787c45ebc37acc30ca49` |

## Đề bài

> A mysterious text file contains something hidden in plain sight. Look carefully at the patterns and uncover the secret.

Archive chỉ có một tệp `challenge.bin`. Dù đuôi là `.bin`, nội dung hoàn toàn là văn bản ASCII, gồm dấu `#`, dấu cách và ký tự xuống dòng. Mục tiêu là tìm thông tin được giấu trong hình ảnh tạo ra từ các ký tự ấy, rồi giải lớp steganography tiếp theo.

## Phân tích — Nhận diện QR dưới dạng ASCII art

Kiểm tra nội dung:

```bash
unzip -l invisiblescan.zip
unzip -p invisiblescan.zip challenge.bin | head -n 12
```

`challenge.bin` dài **15.931 byte**, gồm **89 dòng**, mỗi dòng có **178 ký tự**. Dấu `#` luôn đi thành cặp `##`; hai dấu cách `  ` biểu diễn một ô trắng. Vì vậy mỗi dòng thực chất là 89 ô vuông. Ma trận 89 × 89 gồm một QR code 81 × 81 và viền trắng (quiet zone) rộng 4 ô mỗi phía.

Quy tắc dựng ảnh:

- `##` → 1 module đen.
- `  ` → 1 module trắng.
- Mỗi module nhân lên 8 × 8 pixel để trình quét QR nhận diện ổn định.

Dùng `Pillow` dựng ảnh và `pyzbar` quét mã. Nội dung QR dài **560 byte UTF-8 / 212 ký tự Unicode**, nhưng khi nhìn bằng mắt chỉ thấy:

```text
Congratulations! You found the flag :)
```

Thông báo trên **không phải flag**. Nó còn chứa nhiều ký tự Unicode vô hình xen kẽ giữa các chữ có thể nhìn thấy.

## Phân tích — Unicode vô hình mã hóa mỗi ký tự thành 3 bit

Thống kê chuỗi trả về từ QR cho thấy **38 ký tự ASCII nhìn thấy được** và **174 ký tự Unicode vô hình** thuộc đúng 8 loại. Sắp xếp 8 mã Unicode theo thứ tự code point tăng dần sẽ tạo ra bảng chữ số 0–7:

| Giá trị | Code point | Tên Unicode |
|---:|---|---|
| 0 | `U+200B` | ZERO WIDTH SPACE |
| 1 | `U+200C` | ZERO WIDTH NON-JOINER |
| 2 | `U+200D` | ZERO WIDTH JOINER |
| 3 | `U+2060` | WORD JOINER |
| 4 | `U+2062` | INVISIBLE TIMES |
| 5 | `U+2063` | INVISIBLE SEPARATOR |
| 6 | `U+2064` | INVISIBLE PLUS |
| 7 | `U+FEFF` | ZERO WIDTH NO-BREAK SPACE |

Giữ **nguyên thứ tự xuất hiện** của các ký tự vô hình (bỏ qua các chữ ASCII), chuyển từng giá trị 0–7 thành một số nhị phân 3 bit. Ví dụ, năm ký tự Unicode vô hình đầu tiên là:

```text
U+200B U+200B U+200B U+2060 U+FEFF
   0      0      0      3      7
  000    000    000    011    111
```

174 × 3 = **522 bit**: đọc được **65 byte** đầy đủ và thừa 2 bit cuối (`00`). Chuỗi byte có tiền tố `00 3f`; sau tiền tố là flag ở dạng ASCII:

```text
\x00?kBxAc{a5(Ii_AR7_MasTER_caNv@$_h1DdEn_In_the_piXelS_oF_THE_(ODE}
```

Dùng biểu thức chính quy `kBxAc\{[^}]*\}` để trích xuất trực tiếp từ luồng byte.

## Lời giải — Script tự động tái hiện

Cần Python 3, `Pillow`, `pyzbar` và thư viện `zbar` để quét mã QR. Cài Python packages:

```bash
python -m pip install pillow pyzbar
```

Nếu dùng Linux và thiếu thư viện chia sẻ `zbar`, cài thêm `libzbar0` bằng trình quản lý gói của hệ điều hành.

Lưu đoạn code thành `solve.py` trong thư mục có `invisiblescan.zip`:

```python
#!/usr/bin/env python3
from zipfile import ZipFile
from PIL import Image
from pyzbar.pyzbar import decode
import re

# 1. Chuyển ASCII art thành ma trận QR 89 x 89.
with ZipFile("invisiblescan.zip") as zf:
    rows = zf.read("challenge.bin").decode("ascii").splitlines()

assert len(rows) == 89 and all(len(row) == 178 for row in rows)
qr = Image.new("L", (89, 89), color=255)
for y, row in enumerate(rows):
    for x in range(89):
        cell = row[2*x:2*x+2]
        assert cell in ("##", "  ")
        qr.putpixel((x, y), 0 if cell == "##" else 255)

qr = qr.resize((712, 712), Image.Resampling.NEAREST)
qr.save("invisible_scan_qr.png")
results = decode(qr)
assert results, "Could not decode ASCII-art QR code"
message = results[0].data.decode("utf-8")

# 2. Lọc các ký tự Unicode vô hình khỏi nội dung QR.
visible = "".join(ch for ch in message if ch.isascii())
hidden = [ch for ch in message if not ch.isascii()]
alphabet = sorted(set(hidden))
assert len(alphabet) == 8

# 3. Mỗi code point được ánh xạ thành 3 bit (0..7).
bits = "".join(f"{alphabet.index(ch):03b}" for ch in hidden)
full_bits = len(bits) // 8 * 8  # bỏ các bit cuối không đủ 1 byte
payload = bytes(int(bits[i:i+8], 2) for i in range(0, full_bits, 8))

# 4. Tìm flag trực tiếp trong payload đã giải mã.
match = re.search(rb"kBxAc\{[^}]*\}", payload)
assert match, "Flag not found"

print("QR visible:", visible)
print("Hidden characters:", len(hidden))
print("Hidden bitstream:", len(bits), "bits")
print("Decoded bytes:", len(payload))
print("Flag:", match.group().decode("ascii"))
```

Chạy:

```bash
python solve.py
```

Kết quả đã được kiểm tra với file đề gốc:

```text
QR visible: Congratulations! You found the flag :)
Hidden characters: 174
Hidden bitstream: 522 bits
Decoded bytes: 65
Flag: kBxAc{a5(Ii_AR7_MasTER_caNv@$_h1DdEn_In_the_piXelS_oF_THE_(ODE}
```

## Kết quả

Thử thách có hai lớp giấu tin: **QR được dựng bằng ASCII art** và **luồng bit mã hóa qua tám loại ký tự Unicode vô hình trong nội dung QR**. Chỉ đọc dòng chữ hiển thị sau khi quét QR sẽ bỏ sót dữ liệu thực sự.

```text
kBxAc{a5(Ii_AR7_MasTER_caNv@$_h1DdEn_In_the_piXelS_oF_THE_(ODE}
```
