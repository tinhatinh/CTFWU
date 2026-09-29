---
title: "NAS Coal — Forensics (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Forensics]
tags: [sunshinectf, Forensics]
image:
  path: /CTFWU/SunshineCTF%202026/nas-coal/files/de.png
---
**Flag:** `sun{yup_issa_gem}` · Files: `gem_collection.pptm`, 2229848 byte, sha256 `929726804037cc9b2e8779814aabf88361a6f4035ca1d93803662bdee543e855`

## Đề bài

"someone put coal in my gem collection :'^(" - một file `.pptm` duy nhất, không có
dịch vụ, không có instance. Phải tìm cờ `sun{...}` giấu trong bộ sưu tập "gem".

Tác giả mô tả bài bằng đúng cơ chế của nó: trong xấp toàn thứ quý giá (ảnh đá quý,
meme Pepe) có một thứ "coal" trông vô giá trị - và thứ đó lại là lời giải.

## Phân tích ban đầu

`file` báo `Microsoft PowerPoint 2007+`; đuôi `.pptm` nghĩa là ZIP + VBA. Ba điểm bất
thường thấy ngay:

1. `ppt/media/` có 6 ảnh cho 5 slide: năm file `.png` và một file `.jpg` tên
   `image1.jpg&w=1920&q=75`, kiểu tên sinh ra khi lưu ảnh từ URL của một image
   optimizer. JPEG duy nhất giữa một xấp toàn PNG, đúng chữ "coal" trong đề.
2. `docProps/app.xml` khai `Slides=5, Notes=0, HiddenSlides=0`, nên không có slide ẩn.
3. Slide 5 có một textbox màu accent, chữ `> mfw olevba oneshot chall`.

Điểm 3 là tác giả nói thẳng đáp án. Câu chữ ("mfw" = my fucking reaction) khiến nó đọc
như một câu đùa nên dễ bị bỏ qua.

## Các hướng đã loại

Log đầy đủ ở `notes.md`. Đã kiểm tra và bỏ các kênh sau:

1. ZIP có dữ liệu nối thêm / entry mồ côi: 63 entry, CRC và `compress_size` khớp
   cả hai chiều local↔central, 0 byte không được phủ, không có `extra` hay `comment`.
2. Một "ảnh" thực chất là file khác (`coal.bin`): magic của cả 6 file media và
   thumbnail đều đúng loại khai báo.
3. Bẫy OOXML (`customXml`, `changesInfo`, rels, `[Content_Types]`): chỉ là template
   SharePoint chuẩn.
4. Text ẩn trong slide (chữ trắng, off-canvas, zero-width, notes): quét `<a:t>` trên
   cả slide cộng 11 layout, master và theme, chỉ còn đúng nội dung meme.
5. PNG LSB / bit-plane / alpha / filter-type: quét plane 1 và 2 theo cả hai hướng
   bit, từng kênh và cả ba kênh. Mọi lần chạm header `78 9C`/`1F 8B` đều là nhiễu,
   `zlib` báo lỗi khi giải.
6. JPEG progressive DCT stego: 5 scan đúng khuôn mẫu libjpeg, không segment thừa,
   không có data sau EOI.

## Chuỗi khai thác

**Bước 1 - Đọc macro bằng oletools.** `olevba` mở `ppt/vbaProject.bin` (OLE compound
file nằm trong ZIP) và trích module `MediaCache`:

```bash
pip install --index-url https://pypi.org/simple oletools
olevba gem_collection.pptm
```

```vba
Public Sub RefreshCache()
    Dim encoded As String
    Dim commandLine As String
    encoded = "JABjAGEAbQBwAGEAaQBnAG4AIAA9ACAAJwBzAHUAbgB7AHkAdQBwAF8AaQBzAHMAYQBfAGcAZQBtAH0AJwANAAoA..."
    commandLine = "powershell.exe -NoProfile -EncodedCommand " & encoded
    Debug.Print commandLine
End Sub
```

Nhìn như một mồi nhử: URL `https://gem-cache.example.invalid/coal.bin` dùng TLD
`.invalid` (không tồn tại theo RFC 2606) và macro chỉ `Debug.Print`, không chạy gì.

**Bước 2 - Vẫn giải mã `-EncodedCommand`.** `sun{` không xuất hiện plaintext ở bất
kỳ đâu trong file, nên chuỗi base64 này là chỗ duy nhất có thể chứa cờ. Cờ của bài
này có format riêng `sun{...}` (khác `H7CTF{...}` của mọi bài khác trong cùng giải),
nên phải dò lại toàn bộ file theo đúng prefix đó:

```python
B64_RUN = re.compile(rb"[A-Za-z0-9+/=]{80,}")
FLAG    = re.compile(rb"sun\{[^}\n]{1,120}\}")

for m in B64_RUN.finditer(vba_bin):
    s = m.group(); s = s[: len(s) // 4 * 4]
    for skip in range(4):
        raw = base64.b64decode(s[skip:])
        text = raw.decode("utf-16-le", errors="ignore").encode("latin-1", "ignore")
        if FLAG.search(text):
            yield text
```

`-EncodedCommand` của PowerShell luôn là UTF-16LE, đó là lý do `sun{` không thể
xuất hiện khi grep thô.

**Bước 3 - Kết quả giải mã.** Base64 ở offset 4117 của `vbaProject.bin`, dài 584
byte biểu diễn, decode ra đúng 4 dòng:

```
$campaign = 'sun{yup_issa_gem}'
$source = 'https://gem-cache.example.invalid/coal.bin'
$destination = 'coal.bin'
[pscustomobject]@{Operation='download'; Campaign=$campaign; Source=$source; Destination=$destination}
```

**Bước 4 - Kiểm chứng không còn cờ nào khác.** Sinh mọi biến thể mã hoá (raw,
UTF-16LE/BE, reversed, ROT13, hex, base64 với 4 offset lệch, base64-of-UTF-16,
hex-trong-file) trên 63 entry ZIP đã giải nén, trên pixel đã đảo filter, trên
bit-plane LSB, và trên từng OLE stream. Chỉ có một chuỗi `sun{...}` trong toàn bộ
archive, chính là chuỗi ở Bước 3. Nên nó là cờ, còn mồi nhử thật là năm kênh stego
đã loại ở trên.

## Flag
```bash
python exploit.py files/gem_collection.pptm
```

```
[*] files/gem_collection.pptm -> ppt/vbaProject.bin = 13312 byte
[+] PowerShell -EncodedCommand giai ma duoc:
    $campaign = 'sun{yup_issa_gem}'
    $source = 'https://gem-cache.example.invalid/coal.bin'
    $destination = 'coal.bin'
    [pscustomobject]@{Operation='download'; Campaign=$campaign; Source=$source; Destination=$destination}
[+] CO: sun{yup_issa_gem}
```
