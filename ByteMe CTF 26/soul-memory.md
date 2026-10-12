---
title: "Soul Memory"
category: "Forensics"
tags: ["memory-artifact", "key-value-parsing", "plaintext-flag", "field-locator"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul Memory

**Flag:** `OWASP{s0ul_m3m0ry_n3v3r_d13s}`
**Artifact:** `memory_dump.txt` (148 B theo ghi nhận).

## Đề bài

Đề (Easy, 100 điểm, 25 lời giải trên nền tảng): một bản ghi cache được lấy ra từ "memory dump" của Soul Vault, trong đó một dòng hint chỉ cách xác định trường chứa đáp án.

Toàn bộ nội dung artifact là sáu trường `key=value`:

```text
pid=4041
module=soul-cache
user=keeper
cache_key=MEMORY_7
vault_hint=look_after_after_cache_key
data=OWASP{s0ul_m3m0ry_n3v3r_d13s}
```

## Phân tích

Bốn trường đầu là metadata của bản ghi: `pid=4041`, `module=soul-cache`, `user=keeper` (cùng tên user `keeper` xuất hiện trong các bài nhóm Soul Vault), `cache_key=MEMORY_7`. Hai trường còn lại mang thông tin định vị đáp án.

`vault_hint=look_after_after_cache_key` chỉ tới phần sau `cache_key`. Trường `data` chứa trực tiếp chuỗi `OWASP{...}`.

Áp dụng quy tắc đó trên thứ tự trường đã ghi: tính từ `cache_key=MEMORY_7` trở về sau có hai trường, `vault_hint` và `data`. Trường `vault_hint` chỉ chứa chính câu chỉ dẫn, không phải dữ liệu; trường `data` là trường đầu tiên sau cache key mang một giá trị payload. Giá trị của nó đã ở dạng rõ và đã mang sẵn định dạng cờ:

```text
data=OWASP{s0ul_m3m0ry_n3v3r_d13s}
```

Không tồn tại bước giải mã: giá trị không phải hex, không phải base64, không bị XOR hay nén. Đây là bài đọc và chọn trường, không phải bài biến đổi dữ liệu.

Bài dùng bản text đã lưu; định dạng byte và kích thước file gốc chưa được đối chiếu.

## Lời giải

Trích trường `data` từ bản ghi:

```console
$ python -c "import pathlib,re; t=pathlib.Path('memory_dump.txt').read_text(); print(re.search(r'^data=(\S+)', t, re.M).group(1))"
```

```text
OWASP{s0ul_m3m0ry_n3v3r_d13s}
```

Nếu chỉ làm việc với phần text đã ghi lại, thao tác tương đương là đọc giá trị đứng sau `data=`.

Script minh hoạ việc đọc trường `data`; đọc trực tiếp giá trị trong bản ghi cũng đủ.

```python
import re

record = (
    "pid=4041\n"
    "module=soul-cache\n"
    "user=keeper\n"
    "cache_key=MEMORY_7\n"
    "vault_hint=look_after_after_cache_key\n"
    "data=OWASP{s0ul_m3m0ry_n3v3r_d13s}"
)

fields = [line.split("=", 1) for line in record.splitlines()]
keys = [k for k, _ in fields]
i = keys.index("cache_key")
print("cache_key value :", fields[i][1])
for k, v in fields[i + 1:]:
    print("after cache_key : %-10s -> %r" % (k, v))
```

```text
cache_key value : MEMORY_7
after cache_key : vault_hint -> 'look_after_after_cache_key'
after cache_key : data       -> 'OWASP{s0ul_m3m0ry_n3v3r_d13s}'
```

Trong hai trường được liệt kê, chỉ `data` là payload; `vault_hint` lặp lại chính câu chỉ dẫn.

## Kết quả

```text
OWASP{s0ul_m3m0ry_n3v3r_d13s}
```

Cờ là giá trị của trường `data`; không cần giải mã. Chưa lưu phản hồi submission.

## Tái hiện

Chỉ cần Python 3 (`pathlib`, `re`). Nếu có file `memory_dump.txt`, chạy một lệnh trích trường `data` như trên. Nếu chỉ có bản text ghi lại, lưu `record` trong đoạn script ở mục Lời giải thành `solve.py` rồi chạy:

```console
$ python solve.py
```

Script không đọc file, nên tái hiện được độc lập với việc artifact gốc còn tồn tại hay không.
