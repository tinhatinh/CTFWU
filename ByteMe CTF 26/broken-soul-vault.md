---
title: "Broken Soul Vault"
category: "Forensics"
tags: ["metadata", "hex-decoding", "log-analysis", "file-recovery"]
solve_date: "2026-10-09"
language: "vi"
---

# Broken Soul Vault

**Flag:** `OWASP{br0k3n_s0ul_v4ult_r3c0v3r3d}`
**Artifact:** `metadata.bin.txt` (87 B) và `vault.log` (133 B). Tác giả: Pratik Jadhav.

## Đề bài

Đề (Easy, 100 điểm):

```text
The Soul Vault suffered metadata corruption during a recovery operation. Identify the valid recovered block and decode its contents.
```

Hai file đầu vào: `vault.log` mô tả phiên khôi phục, `metadata.bin.txt` chứa các block metadata đã được "recovered". Yêu cầu là chọn ra block hợp lệ trong số các block bị hỏng rồi giải mã nó.

## Phân tích

`vault.log` có dữ liệu gây nhiễuy dòng, kết thúc bằng một chỉ dẫn trực tiếp tới file metadata:

```text
OPEN vault
AUTH keeper
READ /soul/fragment
ERROR checksum mismatch
RECOVER block=17
RECOVER block=18
NOTE corrupted metadata follows
```

Chuỗi sự kiện là: đọc fragment → checksum mismatch → hai thao tác `RECOVER` (block 17 và 18) → ghi chú rằng phần metadata đi kèm đã bị hỏng. Log không chứa dữ liệu nào ngoài ngữ cảnh, nên toàn bộ nội dung cần giải mã nằm trong `metadata.bin.txt`.

File này chứa ba dòng hex, mỗi dòng một block. Ghi lại nguyên văn:

```text
00ff11aa
4f574153507b6272306b336e5f7330756c5f7634756c745f7233633076337233647d
deadbeef
```

Độ dài các block (tính theo hex ký tự, rồi suy ra số byte):

```text
block 1 :  8 hex chars ->  4 bytes
block 2 : 68 hex chars -> 34 bytes
block 3 :  8 hex chars ->  4 bytes
```

Hai block biên giải mã thành các dãy byte không in được:

```text
block 1 -> 00 ff 11 aa
block 3 -> de ad be ef
```

Đây là hai sentinel thường dùng làm marker dữ liệu hỏng/rác (`00ff11aa` và `deadbeef`), khớp đúng với cảnh báo `corrupted metadata` trong log. Block giữa là block duy nhất chỉ gồm các cặp hex trong khoảng `20`–`7e` sau khi giải mã, tức ASCII in được, và mở đầu bằng `4f 57 41 53 50 7b` = `OWASP{`. Tiêu chí chọn block do đó không dựa vào vị trí mà dựa vào tính hợp lệ của nội dung: chỉ một trong ba block tạo thành chuỗi ASCII có nghĩa.

## Lời giải

Giải mã block giữa:

```console
$ python -c "h='4f574153507b6272306b336e5f7330756c5f7634756c745f7233633076337233647d'; d=bytes.fromhex(h); print(len(d), d.decode())"
```

```text
34 OWASP{br0k3n_s0ul_v4ult_r3c0v3r3d}
```

Cờ dài 34 byte, đúng bằng số byte của block, không có byte thừa hay byte đệm phải cắt.

Script kiểm tra cả ba block một cách tự động, để việc loại hai block biên là kết quả đo được chứ không phải nhận định:

```python
import pathlib

blocks = pathlib.Path("metadata.bin.txt").read_text().split()
for i, h in enumerate(blocks, 1):
    d = bytes.fromhex(h)
    printable = all(32 <= b < 127 for b in d)
    print("block %d: %2d bytes  printable=%-5s  %r" % (i, len(d), printable, d))
```

```text
block 1:  4 bytes  printable=False  b'\x00\xff\x11\xaa'
block 2: 34 bytes  printable=True   b'OWASP{br0k3n_s0ul_v4ult_r3c0v3r3d}'
block 3:  4 bytes  printable=False  b'\xde\xad\xbe\xef'
```

Chỉ block 2 thoả điều kiện in được và cũng là block duy nhất có dạng cờ.

## Kết quả

```text
OWASP{br0k3n_s0ul_v4ult_r3c0v3r3d}
```

Cờ được giải mã trực tiếp từ block thứ hai của `metadata.bin.txt`; hai block còn lại giải mã thành sentinel và bị loại vì không tạo được chuỗi ASCII. Bài này offline, chỉ dùng Python 3, không có dịch vụ remote. Chưa lưu phản hồi submission.

## Tái hiện

Chỉ cần Python 3 (`pathlib`, `bytes.fromhex`), không cần thư viện ngoài. Đặt `metadata.bin.txt` và `vault.log` cùng thư mục rồi chạy:

```console
$ python -c "import pathlib; print(pathlib.Path('vault.log').read_text())"
$ python -c "import pathlib; print(pathlib.Path('metadata.bin.txt').read_text())"
$ python -c "h='4f574153507b6272306b336e5f7330756c5f7634756c745f7233633076337233647d'; print(bytes.fromhex(h).decode())"
```

Để chạy phần phân loại block, lưu đoạn script trong mục Lời giải thành `solve.py` cạnh `metadata.bin.txt` rồi chạy `python solve.py`; script đọc file theo đường dẫn tương đối so với thư mục hiện hành.
