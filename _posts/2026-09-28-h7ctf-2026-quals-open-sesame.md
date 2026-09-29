---
title: "Open Sesame — Hardware (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Hardware]
tags: [h7ctf-quals, Hardware]
image:
  path: /CTFWU/H7CTF%202026%20Quals/open-sesame/files/de.png
---
**Flag:** `H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}` (nhận từ `/unlock`, đã lưu ở `flag.txt`)
**Target:** `https://web-7a56034b5423964c.web.h7tex.com` · Artifact: `capture.cf32` (I/Q float32 LE @ 1 MHz)

## Đề bài

Một remote garage rẻ tiền tự phát code mới mỗi lần bấm, và đề cho đúng 8 lần bấm thu được dưới dạng
baseband thô. Câu gợi ý: "unguessable" không đồng nghĩa với "unpredictable". Việc phải làm là tính code
mà remote sẽ phát ở lần bấm thứ 9 rồi nộp cho service.

## Phân tích ban đầu

`capture.cf32` = I/Q float32 LE @ 1 MHz. Host không có GNU Radio, không có urh, nên giải điều chế tay.

## Các hướng đã loại

1. KeeLoq, hoặc một PRNG mật nào đó đứng sau bộ code. Không cần tới khoá: tách 48 bit thành
   `32 bit cố định | 12 bit counter | 4 bit checksum` thì counter tăng đều `+0x30` qua cả 8 lần bấm, và
   nibble cuối bằng tổng trị số 11 nibble đầu mod 16 trên cả 8 khung. Một bộ sinh công khai mô tả trọn
   capture thì không còn kênh mật nào để đánh.

## Chuỗi khai thác

**Bước 1 - Envelope.** `env = I^2 + Q^2`, làm mượt cửa sổ 20 µs để san ripple trong một chip.

**Bước 2 - Ngưỡng OOK.** `p1 + 0.35*(max - p1)` → 392 burst.

**Bước 3 - Tách lần bấm.** Ngắt theo khoảng lặng > 1.5 ms → đúng 8 press (7 khoảng lặng dài ~10T).

**Bước 4 - Đọc bit trong một press.** Run-length chỉ có hai độ rộng, 1T và 2T với T = 303 µs, và
97 run = 1 + 2×48 → 48 bit, mỗi bit là một cặp (H,L): `H1L2` = 0, `H2L1` = 1.

**Bước 5 - Tám khung thu được.**

```
4f122809be13
4f122809c117
4f122809c41a
4f122809c71d
4f122809ca10
4f122809cd13
4f122809d017
4f122809d31a
```

**Bước 6 - Mô hình rolling code.** Tách 48 bit thành `32 bit cố định | 12 bit counter | 4 bit checksum`:

| press | counter | crc nibble | tổng 11 nibble đầu mod 16 |
| --- | --- | --- | --- |
| 0 | 0xbe1 | 3 | 3 |
| 1 | 0xc11 | 7 | 7 |
| 2 | 0xc41 | a | a |
| 3 | 0xc71 | d | d |
| 4 | 0xca1 | 0 | 0 |
| 5 | 0xcd1 | 3 | 3 |
| 6 | 0xd01 | 7 | 7 |
| 7 | 0xd31 | a | a |

- Counter tăng đều tay `+0x30` qua cả 8 lần bấm.
- `crc = (tổng trị số 11 nibble đầu tiên) mod 16`, khớp cả 8 khung.

Mã đổi mỗi lần bấm thật, nhưng chỉ vì counter đổi. Đó là chỗ "unguessable ≠ unpredictable": bộ sinh là
một counter công khai cộng một checksum tính bằng phép cộng nibble.

**Bước 7 - Dự đoán lần bấm thứ 9.**

```
counter = 0xd31 + 0x30 = 0xd61
frame   = 4f122809 d61  + crc
crc     = (4+15+1+2+2+8+0+9 + 13+6+1) mod 16 = 61 mod 16 = 13 = d
code    = 4f122809d61d
```

**Bước 8 - Kiểm chứng tính đúng.** Hai bất biến trên được kiểm trên toàn bộ 8 khung chứ không phải một
khung: 32 bit đầu giống hệt nhau ở mọi khung, và hiệu counter giữa hai khung liên tiếp luôn là `0x30`.
Với mỗi khung, crc tính lại theo công thức đều đúng bằng nibble cuối.

## Flag
```
python solve.py https://web-7a56034b5423964c.web.h7tex.com analysis/capture.cf32 --submit
[*] /unlock -> 200
{"status": "unlocked", "flag": "H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}"}
```
