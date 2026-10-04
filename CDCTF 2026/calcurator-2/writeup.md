# CalcuRATor (2/4) - Forensics + Rev Eng (500 points)

**Flag:** `cdctf{ICMP ECHO REQUEST}` · **Files:** `files/calculator`, 7868520 bytes, sha256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`

## Đề bài

Tìm loại packet kích hoạt bộ xử lý của backdoor.

## Phân tích ban đầu

Cả bốn file có cùng SHA-256. Phân tích tĩnh bằng Python 3.12 và GNU objdump; không thực thi mẫu.

Hàm `0x12b460` dùng raw socket. Các hằng số truyền vào socket là 2, 3, 1; byte ICMP type được so với 8.

## Các hướng đã loại

HTTP/TLS không phù hợp với hàm đã tìm: socket dùng IPPROTO_ICMP. Echo Request thông thường chỉ vượt qua kiểm tra type, chưa vượt qua kiểm tra khóa.

## Chuỗi khai thác

Tại `0x12b490`, `socket(2,3,1)` tương ứng `AF_INET/SOCK_RAW/IPPROTO_ICMP`. Buffer nhận ở `rsp+0x20`; tại `0x12b4c8`, `[rsp+0x34]` được so với `0x8`. Offset 20 sau IPv4 header là ICMP type, và type 8 là Echo Request.

```bash
objdump -d -M intel --start-address=0x12b460 --stop-address=0x12b536 files/calculator
```

```python
import argparse, hashlib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("artifact", type=Path)
a = p.parse_args()
b = a.artifact.read_bytes()
assert hashlib.sha256(b).hexdigest() == "c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6", "Unexpected artifact"
assert b[0x12b461:0x12b46b] == bytes.fromhex("be03000000bf02000000")
assert b[0x12b48b:0x12b490] == bytes.fromhex("ba01000000")
assert b[0x12b4c8:0x12b4cd] == bytes.fromhex("807c243408")
protocol = {1: "ICMP"}[int.from_bytes(b[0x12b48c:0x12b490], "little")]
packet = {8: "ECHO REQUEST"}[b[0x12b4cc]]
print(f"cdctf{{{protocol} {packet}}}")
```

Flag được suy ra và in bởi script cục bộ; chưa có bằng chứng submission được chấp nhận.

## Flag

```bash
python exploit.py files/calculator
```

```text
cdctf{ICMP ECHO REQUEST}
```

## Reproduce

```bash
python exploit.py files/calculator
```
