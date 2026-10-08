# CalcuRATor (4/4) - Forensics + Rev Eng + OSINT (500 points)

**Flag:** `cdctf{libqalculate/prism}` · **Files:** `files/calculator`, 7868520 bytes, sha256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`

## Đề bài

Xác định hai repository nguồn của calculator và backdoor.

## Phân tích

Cả bốn file có cùng SHA-256. Phân tích tĩnh bằng Python 3.12 và GNU objdump; không thực thi mẫu.

Strings chứa `libqalculate`, `qalc`, biến môi trường QALCULATE và URL tài liệu. Backdoor có raw ICMP receiver, parser callback và sửa argv.

## Hướng đã thử

Các kết quả tìm kiếm icmpdoor/icmpsh không đủ để kết luận chỉ từ cùng giao thức. Repository JadedWraith được thử nhưng trả HTTP 404. PRISM có đối chiếu cụ thể ở parser và cách đổi tên.

## Lời giải

Repository `Qalculate/libqalculate` chứa CLI qalc. `andreafabrizi/prism` có buffer 1024 byte, ICMP_ECHO, parser `%15s %d`, kiểm tra port > 0 và độ dài IP >= 7, fork rồi reverse shell. Code sửa argv bằng strncpy và memset cũng khớp. Bản challenge đổi tên thành wpad và thêm kiểm tra XOR; tên repository dùng trong flag vẫn là libqalculate/prism.

```bash
objdump -d -M intel --start-address=0x12b330 --stop-address=0x12b5a7 files/calculator
```

```python
import argparse, hashlib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("artifact", type=Path)
a = p.parse_args()
b = a.artifact.read_bytes()
assert hashlib.sha256(b).hexdigest() == "c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6", "Unexpected artifact"
assert b"libqalculate\0" in b and b"QALCULATE_USER_DIR\0" in b
assert b"%15s %d\0" in b and b"/bin/sh\0" in b
assert b[0x12b4c8:0x12b4cd] == bytes.fromhex("807c243408")
src = (Path(__file__).parent / "analysis" / "prism.c").read_text()
for token in ["socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)", '"%15s %d"', "strncpy(argv[0], PROCESS_NAME, strlen(argv[0]))"]:
    assert token in src
# Attribution follows the documented manual source comparison, not strings alone.
print("cdctf{libqalculate/prism}")
```

Flag được suy ra và in bởi script cục bộ; chưa có bằng chứng submission được chấp nhận.

Nguồn đối chiếu:

- https://github.com/Qalculate/libqalculate/blob/master/man/qalc.1
- https://github.com/andreafabrizi/prism/blob/master/prism.c

## Kết quả

```bash
python exploit.py files/calculator
```

```text
cdctf{libqalculate/prism}
```

## Tái hiện

```bash
python exploit.py files/calculator
```
