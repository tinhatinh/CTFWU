---
title: "Vormir Common Modulus"
category: "Crypto"
tags: ["rsa", "common-modulus", "bezout"]
solve_date: "2026-10-09"
language: "vi"
---

# Vormir Common Modulus

**Flag:** `OWASP{v0rm1r_tw1st3d_rsa_l34ks_th3_s0ul}`
**Artifact:** `params.txt` (386 B). Tác giả: Pratik Jadhav.

## Đề bài

Đề (Easy, 100 điểm):

```text
Two custodians encrypted the same Soul Vault secret using RSA with a shared modulus but different public exponents. Recover the plaintext.
```

Đầu vào duy nhất là `params.txt`, năm dòng `key = value`:

```text
n = 16380649768533394557837493376413306403300053927332145442950164332328030751564185489519565597585555867737606727528343
e1 = 65537
e2 = 65539
c1 = 13717084049277399427945358975177210874446528287993178469838547381506741616766449871863462627142297960244208456711847
c2 = 4601321998457411971134687661444766716276847022305030736758227088246554672740623255330037934526510403437754437399162
```

## Phân tích

Các giá trị đo trực tiếp từ file, không phải giả định:

```text
n bit_length     : 383
gcd(e1, e2)      : 1
m bit_length     : 319
```

`n` dài 383 bit, nhỏ hơn nhiều mức thông thường của RSA và là con số đo từ `params.txt`, không phải độ dài chuẩn 1024 hay 2048 bit.

Hai cặp `(e1, c1)` và `(e2, c2)` dùng chung một `n`, và dữ liệu gây nhiễun rõ được nói tới là một. Mô hình do đó là:

```text
c1 = m^e1 mod n
c2 = m^e2 mod n
```

Vì `gcd(e1, e2) = 1`, đồng nhất thức Bezout cho `a`, `b` với `a*e1 + b*e2 = 1`, suy ra:

```text
c1^a * c2^b = m^(a*e1 + b*e2) = m  (mod n)
```

toán tử dùng được mà không cần phân tích `n`. Chọn `a = pow(e1, -1, e2)` rồi `b = (1 - a*e1) // e2` cho `a = 32769`, `b = -32768`, kiểm tra lại `32769*65537 - 32768*65539 = 2147581953 - 2147581952 = 1`.

`b` âm nghĩa là `c2^b` cần nghịch đảo của `c2` theo modulo `n`; đây là bước duy nhất ngoài phép luỹ thừa. `a` dương nên `c1` giữ nguyên. Sau bước đổi dấu, số mũ thực tế dùng là `a = 32769` và `b = 32768` với `c2` đã thay bằng `pow(c2, -1, n)`.

`m` thu được 319 bit, vừa đủ chứa 40 byte ASCII của cờ (40*8 = 320 bit, byte đầu nhỏ hơn `0x80`), nhất quán với RSA textbook không padding như đề mô tả.

## Lời giải

Script giải (chỉ stdlib):

```python
from math import gcd
import ast, pathlib

src = pathlib.Path(__file__).with_name("params.txt").read_text()
ns = {}
for line in src.strip().splitlines():
    if line.strip():
        k, v = line.split("=")
        ns[k.strip()] = int(v)

n, e1, e2, c1, c2 = ns["n"], ns["e1"], ns["e2"], ns["c1"], ns["c2"]

assert gcd(e1, e2) == 1, "e1 and e2 not coprime"

# Bezout: a*e1 + b*e2 = 1
a = pow(e1, -1, e2)
b = (1 - a * e1) // e2

if a < 0:
    c1, a = pow(c1, -1, n), -a
if b < 0:
    c2, b = pow(c2, -1, n), -b

m = pow(c1, a, n) * pow(c2, b, n) % n
print("a,b =", (1 - a * e1) / e2, b)
print("m  =", m)

pt = m.to_bytes((m.bit_length() + 7) // 8, "big")
print("pt =", pt)
```

Output:

```text
a,b = -32768.0 32768
m  = 661996120338108837762769633508381563709412516386178580218881506680140567815232126603297643916413
pt = b'OWASP{v0rm1r_tw1st3d_rsa_l34ks_th3_s0ul}'
```

Dòng `a,b` in hai dạng của cùng một hệ số: `-32768.0` là `b` của đồng nhất thức Bezout (phép chia dấu chấm động), `32768` là số mũ dương được dùng sau khi `c2` đã thay bằng nghịch đảo của nó.

Kiểm chứng không dựa vào lời giải thích: mã hoá lại `m` bằng cả hai số mũ và so với ciphertext trong file.

```python
from math import gcd
import pathlib

ns = {}
for line in pathlib.Path("params.txt").read_text().strip().splitlines():
    if line.strip():
        k, v = line.split("=")
        ns[k.strip()] = int(v)
n, e1, e2, c1, c2 = (ns["n"], ns["e1"], ns["e2"], ns["c1"], ns["c2"])

m = 661996120338108837762769633508381563709412516386178580218881506680140567815232126603297643916413
print("n bit_length     :", n.bit_length())
print("gcd(e1, e2)      :", gcd(e1, e2))
print("m bit_length     :", m.bit_length())
print("pow(m, e1, n) == c1 :", pow(m, e1, n) == c1)
print("pow(m, e2, n) == c2 :", pow(m, e2, n) == c2)
print("pt               :", m.to_bytes((m.bit_length() + 7) // 8, "big"))
```

```text
n bit_length     : 383
gcd(e1, e2)      : 1
m bit_length     : 319
pow(m, e1, n) == c1 : True
pow(m, e2, n) == c2 : True
pt               : b'OWASP{v0rm1r_tw1st3d_rsa_l34ks_th3_s0ul}'
```

## Kết quả

```text
OWASP{v0rm1r_tw1st3d_rsa_l34ks_th3_s0ul}
```

Dữ liệu giải mã từ artifact `params.txt` và tự kiểm chứng bằng phép mã hoá lại với `e1` và `e2`; hai phép so sánh ciphertext đều trả `True`. Không có dịch vụ remote cho bài này. Chưa lưu phản hồi submission.

## Tái hiện

Chỉ cần Python 3 (`math`, `pathlib`), không cần thư viện mã hoá. Đặt `solve.py` cùng thư mục với `params.txt` vì script đọc file này theo đường dẫn tương đối so với chính nó, rồi chạy:

```console
$ python solve.py
```

Để chạy độc lập phần kiểm chứng, lưu block thứ hai thành `check_vormir.py` cạnh `params.txt` rồi chạy `python check_vormir.py`; block này hard-code `m` nên phát hiện ngay nếu `params.txt` khác dữ liệu gây nhiễun được dùng ở trên.
