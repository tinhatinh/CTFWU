---
title: "Excavation (RE-100) - Pointer Overflow CTF 2026"
date: 2026-09-29 23:31:27 +0700
lastmod_at: 2026-09-29 23:31:27 +0700
categories: [RE]
tags: [pointer-overflow, RE]
image:
  path: /CTFWU/Pointer%20Overflow%20CTF%202026/excavation/files/de.png
---
{% raw %}
Flag / đáp án được chấp nhận: `2VE5EKXUA5IV2R57`

```
POST /challenges/excavation/submit  {"flag":"2VE5EKXUA5IV2R57"}
{"correct":true,"message":"Correct."}
```

## 1. Bài cho gì

Bốn file `.sav` của một game RPG giả định: ba file mẫu của các run lưu trữ khác nhau, một file `team.sav` sinh riêng cho team và "mang theo một token 16 ký tự". Không có tool đọc file, không có định dạng. Định dạng phải tự suy ra từ chính bốn file.

## 2. Phân tích ban đầu

12 byte đầu của cả bốn file giống hệt nhau:

```
9e e1 c7 21 | 02 00 | 02 00 | d2 01 00 00     sample1
9e e1 c7 21 | 02 00 | 02 00 | 59 03 00 00     sample2
9e e1 c7 21 | 02 00 | 02 00 | 78 04 00 00     sample3
9e e1 c7 21 | 02 00 | 02 00 | 66 05 00 00     team
```

Bốn byte cuối của header là u32 little-endian và đúng bằng kích thước file: 466, 857, 1144, 1382. Nên phần thân bắt đầu từ offset 12, còn header thì không bị mã hoá.

Đo tự tương quan trên phần thân (đếm tỉ lệ `body[i] == body[i+L]`) cho một đỉnh rất rõ ở các bội số của 8:

```
sample1  lag 8 = 0.058, lag 16 = 0.043, lag 24 = 0.044, còn lại <= 0.015
team     lag 8 = 0.045, lag 16 = 0.048, lag 24 = 0.047, còn lại <= 0.008
```

Đó là dấu hiệu của khoá XOR lặp 8 byte.

## 3. Các hướng đã thử và loại

**Dùng chung một khoá cho cả bốn file.** Khoá của `team.sav` chỉ đưa các file khác đạt 10-17% byte thuộc bảng chữ cái, trong khi chính nó đạt 72%. Mỗi file có một khoá riêng:

```
sample1  bff366a0192308a7
sample2  8ee28d4183df8c1b
sample3  e62903e8dcf7b038
team     1337df4e77c16cc7
```

**Plaintext là text thuần.** Sau khi XOR với khoá, `team.sav` vẫn còn 260/1370 byte nằm ngoài vùng in được, và chúng trải đều trên cả 8 cột (28 đến 36 byte mỗi cột). Nên không có cột khoá nào bị sai, và trong file thật sự có field nhị phân.

**Khoá quay theo bản ghi.** Đây là hướng dễ bị nhầm nhất, vì các byte "lạ" chêm vào giữa text đọc được. Nhưng record của cùng một vật phẩm trong hai file khác nhau khớp với nhau từng byte trên các đoạn dài hơn 60 byte:

```
sample1: 21 20 37 72 55 53 54 45 44 00 53 50 49 52 49 54 0d 4d ... 4c 45 00 57 45 49 47 48 54 0e
team   : 21 20 37 72 55 53 54 45 44 00 53 50 49 52 49 54 0d 4d ... 4c 45 00 57 45 49 47 48 54 0e
```

Khoá đúng và plaintext trùng nhau, nên mấy byte kỳ dị kia là dữ liệu thật của file.

**Token là một dãy 16 ký tự trong text.** `re.finditer(rb'[A-Z0-9]{16,}')` và `[A-Za-z0-9_]{14,}` không trả về kết quả nào trên cả bốn file.

**Token là 14 byte cuối của record vị trí cuối cùng.** Bốn file đều kết thúc bằng đúng 14 byte:

```
sample1  00 00 00 00 00 00 fd ff ff ff 8a 3a 82 c6
sample2  30 fd ff 79 05 00 d6 ff ff ff 9c 45 62 ea
sample3  c6 07 00 75 f3 ff e0 ff ff ff c0 51 d5 eb
team     fc fa ff 60 02 00 9f ff ff ff 5f 53 9d 05
```

Chúng là field nhị phân (một `i32` âm, một sentinel `ff ff ff`, bốn byte checksum), độ dài 14 không đổi, không mã hoá cho 16 ký tự. Hướng này sai.

## 4. Mấu chốt: hai lớp, không phải một

Có một chi tiết làm hỏng mọi cách đọc "text thuần": chữ cái **đầu** mỗi từ thì in thường, còn lại in hoa (`mIDDLE RANK OF A DISCONTINUED ORDER`). Cách xử lý tạm thời là `byte < 0x20 -> byte + 0x20` thì text đọc thông, nhưng độ dài các xâu vẫn vô nghĩa.

Bước thật sự quyết định là soi 6 byte đứng trước mọi xâu. Bảng chữ cái trong file là ASCII đã bị XOR với `0x20`, nên `space` thành `0x00`, `-` thành `0x0d`, `.` thành `0x0e`, `'` thành `0x07`, `:` thành `0x1a`, và **các byte độ dài cũng bị lật bit 5**:

```
'/' = 0x2f  ^0x20 = 15   "Obsidian censer"            15 byte
 0x05       ^0x20 = 37   "Fingerprints of five different hands."   37 byte
 0x3c       ^0x20 = 28   "Warm regardless of the room."            28 byte
 0x28       ^0x20 =  8   "K. Ansen"                   8 byte
```

Áp `^ 0x20` cho toàn bộ phần thân thì mọi thứ quy về chuẩn: text Title Case bình thường, space ra space, và các field nhị phân thành số nhỏ hợp lý. Hoá ra phần thân được mã hoá bằng **hai** lớp:

```
body = struct ^ 0x20 ^ key[i % 8]
```

## 5. Định dạng đã đảo ngược

Header 12 byte, không mã hoá:

```
u8[4]  magic 9e e1 c7 21
u16    0x0002
u16    0x0002
u32    kích thước file (LE)
```

Phần thân là một dãy record, mỗi record tự mô tả độ dài của chính nó qua các prefix:

```
record nhân vật   01  u32  u8 namelen  name  ...  u16 item_count  u8 0
record item       10  u8 idx  u8 a  u8 b  u8 namelen  name  u16 desclen  desc
record nhật ký    02/03  u8 0  u8 idlen  "S<run>D<n>"  u16 desclen  text
record vị trí     04  u32  u8 5  u32 size  u8 namelen  name  14 byte cuối
```

Điểm cần nhớ khi tự viết parser: độ dài xâu tên là `u8`, độ dài xâu mô tả là `u16 LE`, và cả hai đều phải lật bit 5.

Đếm được số item khớp với con số lưu trong record nhân vật:

| file | item_count | số record `0x10` parse được |
|---|---|---|
| sample1 | 5 | 5 |
| sample2 | 10 | 10 |
| sample3 | 13 | 13 |
| team | 16 | 16 |

## 6. Token

Đề đã nhắc sẵn: *"The flag for this challenge is a little different"*, và trong nhật ký của `team.sav` có câu *"I notice its voice most in the items I've collected in a particular order. First things first, I think."*

Lấy chữ cái đầu của tên vật phẩm theo đúng thứ tự túi đồ:

```
sample1  Talcum-stained token, Obsidian censer, Rusted spirit-medallion,
         Cracked seance disc, Hair-braid amulet
         -> TORCH

sample2  Silver-thread bandage, Ivory dial-plate, Lead-bound envelope,
         Vessel-key, Ember-in-glass, Rusted spirit-medallion, Marrow-quill pen,
         Obsidian censer, Obsidian censer, Needle of the Bureau
         -> SILVERMOON

sample3  Needle, Ivory, Ghost-key, Hair-braid, Talcum, Ember, Needle,
         Doubling mirror, Silver, Silver, Obsidian, Obsidian, Needle
         -> NIGHTENDSSOON          ("NIGHT ENDS SOON")
```

Ba mẫu đều là tiếng Anh có nghĩa, nên quy tắc đã được chứng minh bằng dữ liệu của chính tác giả chứ không phải do đoán. `team.sav` có 16 item và cho ra đúng 16 ký tự:

```
 0 2-star runic band        -> 2      8  Ash-glazed lantern        -> A
 1 Vessel-key               -> V      9  5-knot cord               -> 5
 2 Ember-in-glass           -> E     10  Ivory dial-plate          -> I
 3 5-knot cord              -> 5     11  Vessel-key                -> V
 4 Ember-in-glass           -> E     12  2-star runic band         -> 2
 5 Knotted willow charm     -> K     13  Rusted spirit-medallion   -> R
 6 Xylophone plate          -> X     14  5-knot cord               -> 5
 7 Uncoiling rope           -> U     15  7-day candle              -> 7
```

```
2VE5EKXUA5IV2R57
```

Ba item có tên bắt đầu bằng chữ số (`2-star runic band`, `5-knot cord`, `7-day candle`) chỉ xuất hiện trong `team.sav`, không có trong ba file mẫu. Đó là các item tác giả tạo thêm để mã hoá được chữ số trong token của team.

Nộp token:

```
$ curl -s -X POST https://pointeroverflowctf.com/challenges/excavation/submit \
    -H 'Content-Type: application/json' -b cookies.txt \
    -d '{"flag":"2VE5EKXUA5IV2R57"}'
{"correct":true,"message":"Correct."}
```

Dạng bọc `POCTF{2VE5EKXUA5IV2R57}` bị từ chối (`Incorrect. Keep working.`), và endpoint không trả về xâu flag nào để ghi lại. Trang challenge hiển thị `>> ACK :: Correct.`.

## 7. Chạy lại

```
cd excavation
python exploit.py
```

`exploit.py` tự phục hồi khoá 8 byte của cả bốn file (không nhập tay khoá nào), tách lớp `^0x20`, parse record `0x10` và in ra acrostic. Khóa được chọn theo mô hình phân bố byte học từ chính file giải mã tốt nhất, nên `sample3` cũng ra đúng khoá (`e62903e8dcf7b038`) thay vì lệch một byte như cách chấm điểm thô.

Các file trung gian trong `analysis/`: `*.pt` là thân sau lớp XOR thứ nhất, `*.dec` là bản đọc tạm bằng quy tắc `+0x20` cho riêng byte điều khiển, `*.true` là struct thật sau cả hai lớp.

{% endraw %}
