---
title: "The Keeper's Trail"
category: "OSINT"
tags: ["lsb-stego", "qr-decode", "encrypted-pdf", "aes-cbc", "artifact-chain"]
solve_date: "2026-10-09"
language: "vi"
---

# The Keeper's Trail

**Flag:** `OWASP{YouAreTheOne}`
**Artifact:** `Letter.png`, `key-qr.png`, `keeper.pdf`, `hidden.txt` và các kết quả trung gian đã lưu.

## Đề bài

Toàn bộ mô tả có trong thư mục run là tệp `Question.md` (356 B, dòng kết thúc kiểu CRLF). Nguyên văn phần văn dữ liệu gây nhiễun:

```text
An old keeper has been waiting a long time for someone worthy. He's left something behind — a letter. Everything else is inside it.

Read it carefully. Nothing here is just decoration.

Any encryption you encounter uses AES-256 in CBC mode, with keys derived via SHA-256. The algorithm was never the puzzle.
```

Cuối tệp là khối định dạng cờ `OWASP{...}`.

Bản ghi hiện có tái hiện được bước QR → mật khẩu → PDF. Các bước trích QR từ ảnh gốc và giải AES chưa đầy đủ.

## Phân tích

### Danh sách artifact

```text
Question.md        356 B  challenge text
Letter.png     6,894,219 B  PNG 1245 x 2245 RGBA
lsb-0.bin        349,379 B  bit plane 0
lsb-1.bin        349,379 B  bit plane 1
lsb-2.bin        349,379 B  bit plane 2
lsb-3.bin        349,379 B  bit plane 3
lsb-012.bin    1,048,135 B  planes 0+1+2
lsb-0123.bin   1,397,513 B  planes 0+1+2+3
layer1.txt           311 B  34 x 34 palette PNG behind leading junk bytes
key-qr.png           295 B  PNG 162 x 162, mode P
pdf-password.txt      12 B  FewerReturns
keeper.pdf     2,681,960 B  %PDF-1.4, encrypted
keeper-page.png 5,313,846 B  rendered PDF page
pdf-text.txt       782 B  letter text
hidden.txt         642 B  0x + 640 hex chars
flag.txt            19 B  OWASP{YouAreTheOne}
```

Cỡ các dữ liệu gây nhiễun dump LSB khớp đúng phép tính bit-plane của ảnh gốc:

```python
n = 1245 * 2245
print(n, [(k * n + 7) // 8 for k in (1, 3, 4)])
```

```text
2795025 [349379, 1048135, 1397513]
```

Bốn tệp `lsb-0..3.bin` dài đúng 349,379 B = một mặt phẳng bit của 2,795,025 điểm ảnh; `lsb-012.bin` và `lsb-0123.bin` khớp lần lượt 3 và 4 mặt phẳng. Về kích thước, chúng là dữ liệu trích từ `Letter.png`. Đây là kiểm tra kích thước, không phải kiểm tra nội dung: các byte của từng mặt phẳng không được dựng lại từ ảnh khi viết bài.

### Cờ và các giá trị đã khoá

`flag.txt` 19 B chứa `OWASP{YouAreTheOne}` và không có byte xuống dòng cuối (19 ký tự = 19 byte). `pdf-password.txt` cũng không có byte cuối dòng: 12 ký tự = 12 byte, giá trị `FewerReturns`.

Chuỗi `YouAreTheOne` chỉ xuất hiện trong `flag.txt`. Tìm chuỗi này trong `Letter.png`, `keeper.pdf`, `keeper-page.png`, cả sáu tệp LSB, `key-qr.png` và `layer1.txt` đều cho 0 kết quả — cờ không nằm dưới dạng văn dữ liệu gây nhiễun rõ trong bất kỳ artifact nào khác của thư mục.

## Lời giải

### Mã QR mở khoá tệp PDF

`key-qr.png` là ảnh 162×162. Giải bằng OpenCV:

```console
$ python - <<'PY'
> import cv2
> im = cv2.imread("key-qr.png")
> print(cv2.QRCodeDetector().detectAndDecode(im)[0])
> PY
FewerReturns
```

Chuỗi giải mã được dài 12 ký tự, trùng khít giá trị trong `pdf-password.txt`. Mắt xích này do đó có tệp đại diện ở cả hai đầu: QR ở một đầu, mật khẩu ở đầu kia.

Dùng mật khẩu đó mở `keeper.pdf`:

```console
$ python - <<'PY'
> from pypdf import PdfReader
> r = PdfReader("keeper.pdf")
> print("encrypted:", r.is_encrypted, "| decrypt ->", r.decrypt("FewerReturns"))
> print("pages:", len(r.pages))
> PY
encrypted: True | decrypt -> 2
pages: 1
```

`decrypt()` trả về giá trị thành công và trích được văn dữ liệu gây nhiễun. Nội dung trích mới dài 757 ký tự, `pdf-text.txt` lưu 759 ký tự (782 byte thô do dòng kết thúc CRLF): cùng một bức thư, lệch 2 ký tự ở phần whitespace cuối, không đồng nhất từng byte sau khi chuẩn hoá.

### Bức thư của Keeper

`pdf-text.txt` chứa bức thư. Các dòng dẫn tới bước tiếp theo:

```text
Go back to where this journey
started. Not for another door, but for
what you overlooked the first time,
waiting since before you arrived.
There are three that matter. I already
signed one of them into what I gave
you. The other two are close by,
indistinguishable from everything
around them, until you know what
makes a number worth choosing.
Alone, none of them are the stone.
Only together, multiplied as one, do
they become what you came here for.
```

Và phần kết, chép nguyên văn kể cả các fragment hex:

```text
Regards, 
3061
0x107e61259ce9189f0674f5b9e040e69a8
8083053327714a65be2f59558614f045e666
f383b1ae60ebb2cdbaf98143f37
```

`hidden.txt` là một blob hex: `0x` rồi 640 ký tự, tức đúng 320 byte, và `320 % 16 == 0` — 20 block 16 byte, dạng phù hợp với AES-CBC như `Question.md` mô tả.

So sánh với các fragment trong thư:

- Fragment đầu của thư, bỏ tiền tố `0x`, dài 33 ký tự hex; 32 ký tự đầu của nó (`107e61259ce9189f0674f5b9e040e69a` = 16 byte) chính là phần mở đầu của `hidden.txt`. Ký tự thứ 33 trong thư là `8`, còn `hidden.txt` tiếp bằng `a`. Nói cách khác dòng đầu ở cuối thư là dữ liệu gây nhiễun cắt của khối mật ngữ, bị lấy thừa một nibble.
- Hai fragment còn lại (`8083053327714a65be2f59558614f045e666`, `f383b1ae60ebb2cdbaf98143f37`) không xuất hiện trong `hidden.txt`, kể cả 16 byte đầu của chúng.
- Số `3061` không xuất hiện trong `hidden.txt`.

Ba con số mà thư nhắc vì thế không ghép thành khối mật ngữ theo cách nào có thể đọc ra từ tệp; chúng là dữ kiện của bước suy khoá, và bước đó không có artifact.

### Giới hạn tái hiện

Bản ghi thiếu cách trích `key-qr.png` từ `Letter.png`, nguồn của `hidden.txt` và key/IV cho AES-256-CBC. Cờ được lưu trong `flag.txt`, nhưng chưa tái hiện được bước giải `hidden.txt` ra cờ.

## Kết quả

```text
OWASP{YouAreTheOne}
```

Cờ lấy từ `flag.txt` đã lưu. Các lệnh trong bài kiểm tra QR, mật khẩu PDF và nội dung thư; chúng chưa dựng lại được phép giải AES cuối cùng.

## Tái hiện

Những bước sau chạy được hoàn toàn bằng artifact trong thư mục run, cần Python 3 với `opencv-python` (`cv2`), `pypdf` và `Pillow`:

```console
$ cd "C:/Users/Administrator/Downloads/ctf-skills-main/ctf-skills-main/work/keepers-trail/"
$ python -c "from PIL import Image; print(Image.open('Letter.png').size, Image.open('Letter.png').mode)"
(1245, 2245) RGBA
$ python -c "import cv2; print(cv2.QRCodeDetector().detectAndDecode(cv2.imread('key-qr.png'))[0])"
FewerReturns
$ python -c "
from pypdf import PdfReader
r = PdfReader('keeper.pdf')
print(r.is_encrypted, r.decrypt('FewerReturns'), len(r.pages))
print(''.join(p.extract_text() or '' for p in r.pages)[:60])
"
```

Chưa đủ dữ liệu để tái hiện bước trích QR từ `Letter.png` và bước dẫn xuất key/IV cho AES.

Cờ `OWASP{YouAreTheOne}` tồn tại dưới dạng giá trị đã ghi nhận trong `flag.txt`, không phải output của các lệnh trên.
