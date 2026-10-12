---
title: "Soul in the Shadows"
category: "Steg"
tags: ["png", "lsb", "zsteg", "crib-drag", "repeating-key-xor"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul in the Shadows

**Flag:** `OWASP{the_soul_was_here}`
**Artifact:** `Soul_in_the_Shadows_Player - 247 TANISHK MALGE.zip` (2,109,285 B), giải nén thành `archive.png` (2,108,924 B, md5 `bd736a6daca2e56f7ead89a7cbe5976e`) và `challenge.txt` (116 B). Tác giả: Pratik Jadhav.

## Đề bài

Easy, 100 điểm. Đề cho một file nén chứa một ảnh PNG và một file text gợi ý. `challenge.txt` (116 B) chỉ nói chung:

```text
Soul in the Shadows

There is more to this image than what you can see.

Recover the flag.

Flag format: OWASP{...}
```

Ảnh là một khung cảnh tối, không có chữ nào đọc trực tiếp được; payload nằm trong các bit thấp của dữ liệu ảnh và bị XOR bằng một khoá lặp ngắn.

## Phân tích

### Bọc ngoài file nén

`unzip -l` cho hai thành viên, `archive.png` 2,108,924 B và `challenge.txt` 116 B. Định dạng PNG xác nhận bằng `file`: 1000×1180, 8-bit RGB, không có bảng màu, không có alpha.

Layout chunk cho thấy không có dữ liệu giấu kiểu append:

```text
IHDR, 3 x tEXt, 33 x IDAT, IEND, 0 trailing bytes
```

Không còn byte nào phía sau `IEND`, nên mọi hướng soi file thứ hai / zip lồng trong đuôi ảnh đều bị loại ngay từ đầu. Ba chunk `tEXt` có cặp keyword/value:

```text
Title   : Forgotten Record
Author  : Archives
Comment : Some things are left behind on Vormir.
```

`Comment` là gợi ý duy nhất về mặt nội dung (`Vormir`); `Title` và `Author` chỉ là nhãn.

### Quét LSB

Script LSB tự viết trên planes RGB và một script quét theo thứ tự độ sáng đều trả về `hits: 0` trên cùng ảnh này. `zsteg -a` tìm thấy payload ở cấu hình `b1,rgb,lsb,xy` — tức bit thấp nhất của ba kênh RGB, duyệt từng hàng ảnh theo cấu hình `xy` của zsteg:

```text
The archive was checked twice.
GRgTHhkpIic3Ejo9IyMNOighCSc3Pywv
The records showed nothing unusual.
::END::
```

Hàng base64 ở giữa là payload; hai câu tiếng Anh bao quanh và marker `::END::` là phần đánh lừa, không mang dữ liệu.

## Lời giải

Giải mã dòng base64 thu được đúng 24 byte:

```text
1918131e1929222737123a3d23230d3a28210927373f2c2f
```

24 byte là độ dài điển hình của cờ dạng `OWASP{...}`, và 6 byte đầu của mọi cờ trong giải là `OWASP{`. Crib dragging đoạn known-plaintext này trên chính 24 byte cho ra chuỗi lặp:

```python
import base64
ct = base64.b64decode("GRgTHhkpIic3Ejo9IyMNOighCSc3Pywv")
known = b"OWASP{"
key = bytes(c ^ k for c, k in zip(ct, known))
print(len(ct), ct.hex())
print(key)
print(bytes(c ^ key[i % len(key)] for i, c in enumerate(ct)))
```

```text
24 1918131e1929222737123a3d23230d3a28210927373f2c2f
b'VORMIR'
b'OWASP{the_soul_was_here}'
```

Khoá là `VORMIR` (6 byte, chu kỳ 4 lần trên 24 byte mật mã). Giả sử chu kỳ 6 chỉ được xác nhận bởi 6 byte known-plaintext; bằng chứng cho giả định đó là toàn bộ 24 byte còn lại giải mã thành chuỗi in được và có cấu trúc `OWASP{...}` đóng ngoặc đúng, chứ không phải do phỏng đoán.

Lần phân tích độc lập thứ hai trên cùng file ghi nhận:

```text
derived key from OWASP{ prefix: b'VORMIR'
byte offset of message in LSB stream: 0
```

`byte offset ... : 0` nghĩa là payload bắt đầu ngay từ bit thấp đầu tiên của stream, không có phần đệm phía trước; cả hai lượt đều cho ra cùng một cờ.

## Kết quả

```text
OWASP{the_soul_was_here}
```

Cờ được trích từ chính artifact (LSB plane `b1,rgb,lsb,xy`), giải mã bằng khoá XOR dẫn xuất từ known-plaintext và đã được kiểm chứng lại bằng một lượt phân tích độc lập trên cùng file; không có phản hồi submission được lưu.

## Tái hiện

Cần: `unzip`, `file`, Python 3 (`base64`), `zsteg` (đã kiểm chứng ở bản hỗ trợ `-a`).

```console
$ unzip "Soul_in_the_Shadows_Player - 247 TANISHK MALGE.zip"
$ file archive.png
$ md5sum archive.png
$ zsteg -a archive.png
```

Kiểm tra layout chunk và số byte sau `IEND` bằng `list_chunks.py`:

```python
import struct, collections
d = open("archive.png", "rb").read()
i, order, texts = 8, [], []
while i + 8 <= len(d):
    ln = struct.unpack(">I", d[i:i+4])[0]
    t = d[i+4:i+8].decode("latin1")
    order.append(t)
    if t == "tEXt":
        texts.append(d[i+8:i+8+ln].decode("latin1"))
    i += 12 + ln
print(collections.Counter(order), "trailing:", len(d) - i)
for x in texts:
    print(x)
```

Script chỉ đọc header và các chunk đã biết độ dài, không giải mã pixel. Dòng base64 in ra bởi `zsteg -a` là đầu vào của đoạn Python ở mục Lời giải, nên phần còn lại của lời giải không cần chạm tới ảnh.
