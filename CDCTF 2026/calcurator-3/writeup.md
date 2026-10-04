# CalcuRATor (3/4) - Forensics + Rev Eng (500 points)

**Flag:** `cdctf{1CMP_TR1GG3R$}` · **Files:** `files/calculator`, 7868520 bytes, sha256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`

## Đề bài

Khôi phục thông tin còn thiếu trong payload của ICMP Echo Request.

## Phân tích ban đầu

Cả bốn file có cùng SHA-256. Phân tích tĩnh bằng Python 3.12 và GNU objdump; không thực thi mẫu.

Sau kiểm tra type, byte đầu payload phải là `c`; 19 byte tiếp theo đi qua vòng so sánh XOR.

## Các hướng đã loại

Chỉ gửi Echo Request chưa đủ: nhánh tại `0x12b4cf` và vòng XOR vẫn từ chối payload không đúng. Chuỗi ở `0x5c62db` cũng không phải khóa plaintext vì byte nhận được bị XOR trước khi so sánh.

## Chuỗi khai thác

Byte payload ở offset 28 phải bằng `0x63`. Vòng lặp `0x12b500` dùng key tại `0x5e700f`, chỉ số 2..20, so với target tại `0x5c62db`, chỉ số 1..19. Phục hồi bằng target XOR key và thêm byte `c` ở đầu. Sau khóa còn cần địa chỉ callback và cổng, đọc bằng `%15s %d`; cổng phải dương và địa chỉ dài ít nhất 7 ký tự để tới nhánh callback.

```bash
objdump -d -M intel --start-address=0x12b4c8 --stop-address=0x12b5a7 files/calculator
```

```python
import argparse, hashlib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("artifact", type=Path)
a = p.parse_args()
b = a.artifact.read_bytes()
assert hashlib.sha256(b).hexdigest() == "c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6", "Unexpected artifact"
assert b[0x12b4cf:0x12b4d4] == bytes.fromhex("807c243c63")
target = b[0x5c62db:0x5c62db + 21]
key = b[0x5e700f:0x5e700f + 24]
trigger = b"c" + bytes(target[i - 1] ^ key[i] for i in range(2, 21))
print(trigger.decode())
```

Flag được suy ra và in bởi script cục bộ; chưa có bằng chứng submission được chấp nhận.

## Flag

```bash
python exploit.py files/calculator
```

```text
cdctf{1CMP_TR1GG3R$}
```

## Reproduce

```bash
python exploit.py files/calculator
```
