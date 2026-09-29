---
title: "Suntrail — Misc (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Misc]
tags: [sunshinectf, Misc]
image:
  path: /CTFWU/SunshineCTF%202026/suntrail/files/de.png
---
**Flag:** `sun{qwerty_sucks}` · **Files:** `files/suntrail.klc`, 419 byte ASCII, sha256 `abe7590751412fe5607bacd7bfc4a3131e5c108bf2eedbbe78d438e96dc8c6ff`

## Đề bài

`im lost, but you can find the way!`

Một file duy nhất, không có instance từ xa, không có hint cần mở. Tác giả oatzs.

## Phân tích ban đầu

`.klc` là file nguồn của Microsoft Keyboard Layout Creator, không phải file license Kaspersky như
tên gọi dễ gây nhầm. Đầu file là `KBD kbdusx "US"`, rồi khối `SHIFTSTATE`, rồi `ENDKBD`.

Khối `LAYOUT` có 18 dòng tab-separated, mỗi dòng là một phím:

```
10  Q  0  2192  0073  -1
```

Theo thứ tự: mã scan, nhãn phím, trạng thái shift, ký tự unicode ở state 0, ký tự unicode ở state 1,
và `-1`. Hai state không đối xứng:

- state 0 chỉ dùng bốn giá trị: `U+2192` (mũi tên phải, 4 phím), `U+2196` (chéo lên, 4 phím),
  `U+2198` (chéo xuống, 6 phím), `U+25A0` (ô đen, 1 phím ở H);
- state 1 chỉ là chữ thường cùng `{`, `}`, `_`; `U+007B` nằm trên X, `U+007D` nằm trên H.

Ô đen và dấu `}` cùng nằm trên H, nên H là đích. Mỗi phím do đó mang hai lớp: một hướng đi và một
ký tự thu thập được.

## Các hướng đã loại

1. `.klc` là license key của Kaspersky: nội dung là ASCII theo đúng khuôn `KBD` / `SHIFTSTATE` /
   `LAYOUT` / `ENDKBD`. Loại.
2. Dữ liệu ẩn ở byte thừa hoặc khoảng trắng cuối dòng: file kết thúc bằng `ENDKBD\n`, LF thuần,
   không dòng nào có trailing space hay tab, không có byte sau EOF. Loại.
3. Cờ nằm thẳng trong file: triage báo 0 hit mẫu cờ; ký tự trong file chỉ là chữ thường và mũi tên.
   Loại.

Log từng nhánh ở `notes.md`.

## Chuỗi khai thác

**Bước 1 - tách dữ liệu.** Parse 18 dòng `LAYOUT`, bỏ `SPACE` (mã scan `0x39`, hai state đều là dấu
cách nên không mang gì). Xếp 17 phím còn lại thành ba hàng vật lý theo mã scan: top `Q W E R T`,
home `A S D F G H`, bottom `Z X C V B N`.

**Bước 2 - xác định hình học bằng quét không gian nhỏ.** Bàn phím thật so le nên không đoán được
mũi tên chéo tương ứng ô nào. `analysis/search_geometry.py` quét toàn bộ 8³ cách gán ba ký tự hướng
vào tám ô láng giềng, đi thử từ mọi phím với mỗi cách gán, và giữ lại các đường cho ra chuỗi chứa cả
`{` lẫn `}`. Lưới này không cho một nghiệm duy nhất: `analysis/geometry_search_results.txt` lưu 21
đường, phần lớn là chuỗi cụt hoặc thiếu ký tự đầu. Bộ gán còn lại sau bước 3:

```
U+2192 -> sang phải một cột
U+2196 -> lên một hàng
U+2198 -> xuống một hàng
U+25A0 -> điểm dừng
```

**Bước 3 - điểm khởi động suy ra từ đồ thị.** Với hình học ở bước 2, đếm phím không bị mũi tên nào
trỏ vào: chỉ còn `Q`. Đi từ `Q` theo mũi tên đến khi gặp ô đen, đường đó đi qua đúng 17/17 phím, mỗi
phím một lần, và là đường duy nhất trong 21 đường đọc được một chuỗi trọn ven.

```
Q A Z X S W E D C V F R T G B N H
s u n { q w e r t y _ s u c k s }
```

## Flag
```bash
python exploit.py files/suntrail.klc
```

```
keys with no incoming arrow (candidate starts): ['Q']
  start=Q path=QAZXSWEDCVFRTGBNH -> 'sun{qwerty_sucks}'
start key : Q
path      : QAZXSWEDCVFRTGBNH
keys used : 17/17
flag      : sun{qwerty_sucks}
```

## Reproduce

`exploit.py` chỉ dùng stdlib, đọc đường dẫn artifact từ argv, thoát mã 0 khi tìm được đường đi trọn
ven tới ô đích và in ra chuỗi cờ. `analysis/search_geometry.py` là bước dò hình học, kết quả ở
`analysis/geometry_search_results.txt`.
