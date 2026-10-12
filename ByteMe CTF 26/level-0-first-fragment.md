---
title: "Level 0 — First Fragment"
category: "Misc"
tags: ["general-skills", "qr-code", "tile-reassembly", "winzip-aes", "pbkdf2", "opencv", "pyzbar"]
solve_date: "2026-10-09"
language: "vi"
---

# Level 0 — First Fragment

**Flag:** `OWASP{Th3_f1rst_fr4gm3nt}`
**Artifact:** `pieces_0.zip` — 5,672 B; 9 PNG tile, mỗi tile 400×400, tổng dung lượng giải nén 7,440 B.

## Đề bài

Bài là mức đầu tiên của một chuỗi ba mức ("Level 0/1/2") trong sự kiện. Thẻ bài được lưu với chuyên mục General Skills; tên bài lấy từ dữ liệu gây nhiễung các bài đã giải của sự kiện, và thẻ không ghi số điểm cũng như mô tả dài.

## Phân tích

### Archive

`pieces_0.zip` có 9 entry nén kiểu WinZip AE (compress_type 99, vendor `AE`, strength 3 = AES-256). Mỗi entry lưu một giá trị xác thực mật khẩu 2 byte dẫn xuất bằng PBKDF2-HMAC-SHA1 1000 vòng từ salt của chính entry, nên thử một ứng viên mật khẩu chỉ tốn một lần dẫn xuất khoá và kiểm tra được ngoại tuyến mà không cần giải nén. Mật khẩu thu được là `OWASP`; 7-Zip xác nhận trên toàn bộ archive:

```console
$ 7z t -pOWASP pieces_0.zip
7-Zip 21.04 beta (x64) : Copyright (c) 1999-2021 Igor Pavlov : 2021-11-02

Scanning the drive for archives:
1 file, 5672 bytes (6 KiB)

Testing archive: pieces_0.zip
--
Path = pieces_0.zip
Type = zip
Physical Size = 5672

Everything is Ok

Folders: 1
Files: 9
Size:       7440
Compressed: 5672
```

### Nội dung sau khi giải nén

Chín tệp `piece_001.png` … `piece_009.png`, tất cả đều 400×400. Không tệp nào đọc được: mỗi tệp chỉ chứa một phần của một QR code, và phần đó bị cắt ngang các module.

Kích thước ghép: 3 tile × 400 px = 1200 px mỗi cạnh. Một QR version 6 có 41 module mỗi cạnh, cộng dải quiet zone bắt buộc 4 module mỗi phía thành 49 module. Trên khung 1200 px, mỗi module tương ứng `1200/49 = 24.4897…` px, tức cạnh một tile dài `400 / 24.4897 ≈ 16.33` module — không nguyên. Hệ quả: có các module bị cắt ngang đường nối, nên việc đặt sai chỗ một tile sẽ làm hỏng cả finder pattern lẫn các hàng timing, và không có cách đọc nào bỏ qua bước ghép.

Số hoán vị cần xét là `9! = 362.880`. Ràng buộc quiet zone giảm tập đó xuống một cách chọn: các tile nằm trên biên của ảnh ghép mang một dải trắng đều dọc theo cạnh ngoài của chúng, tile góc có hai dải như vậy, còn tile giữa không có dải nào. Kiểm tra độ đều của các dải mép định vị được từng tile vào ô của nó.

## Lời giải

```python
"""Level 0 -- tile reassembly by the quiet-zone test, then QR decode."""
import glob
import os

import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

TILES = {os.path.basename(p): p for p in glob.glob("pieces_0/piece_*.png")}
print("tiles=%d  sizes=%s" % (len(TILES), {Image.open(p).size for p in TILES.values()}))

GRID = [["piece_008.png", "piece_001.png", "piece_009.png"],
        ["piece_005.png", "piece_003.png", "piece_004.png"],
        ["piece_007.png", "piece_002.png", "piece_006.png"]]
assert sorted(t for row in GRID for t in row) == sorted(TILES), "not a permutation"

canvas = Image.new("L", (1200, 1200), 255)
for r, row in enumerate(GRID):
    for c, name in enumerate(row):
        canvas.paste(Image.open(TILES[name]).convert("L"), (c * 400, r * 400))
print("assembled", canvas.size, " module size 1200/49 =", 1200 / 49)

print("cv2    :", repr(cv2.QRCodeDetector().detectAndDecode(np.array(canvas))[0]))
print("pyzbar :", [d.data.decode() for d in decode(canvas.convert("RGB"))])
```

```text
tiles=9  sizes={(400, 400)}
assembled (1200, 1200)  module size 1200/49 = 24.489795918367346
cv2    : 'SOUL STONE // FIRST FRAGMENT // OWASP{Th3_f1rst_fr4gm3nt}'
pyzbar : ['SOUL STONE // FIRST FRAGMENT // OWASP{Th3_f1rst_fr4gm3nt}']
```

Ảnh ghép được đọc bởi hai bộ giải mã độc lập (OpenCV và pyzbar) và cho cùng một chuỗi, nên kết quả không phụ thuộc vào một thư viện đọc QR cụ thể nào. Phần nằm ngoài ngoặc cờ là nhãn của chuỗi bài: `SOUL STONE // FIRST FRAGMENT //`.

Ở mức này các tile đã đúng hướng, không cần xoay.

## Kết quả

```text
OWASP{Th3_f1rst_fr4gm3nt}
```

Cờ giải mã từ artifact: chuỗi đọc được sinh ra từ ảnh ghép 1200×1200 của chính 9 tile trong `pieces_0.zip`, và được xác nhận độc lập bởi hai bộ giải mã QR. Bảng các bài đã giải của sự kiện ghi nhận Level 0 ở trạng thái đã giải.

## Tái hiện

Cần Python 3 kèm `Pillow`, `opencv-python`, `pyzbar` (hoặc `zbar`), và một tool mở được WinZip AE — 7-Zip là cách gọn nhất; nếu muốn tự kiểm mật khẩu thì viết script dẫn xuất PBKDF2-HMAC-SHA1 1000 vòng và so 2 byte xác thực của từng entry. Toàn bộ lời giải chạy ngoại tuyến.

```console
$ 7z x -pOWASP -o./out pieces_0.zip
$ python level0_repro.py
```

Lưu đoạn script trong mục Lời giải thành `level0_repro.py` và chạy trong thư mục chứa `pieces_0/piece_001.png` … `piece_009.png` sau khi giải nén.
