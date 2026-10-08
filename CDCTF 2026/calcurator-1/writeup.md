# CalcuRATor (1/4) - Forensics + Rev Eng (491 points)

**Flag:** `cdctf{wpad}` · **Files:** `files/calculator`, 7868520 bytes, sha256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`

## Đề bài

Tìm tên mà thành phần độc hại tự đổi thành sau khi khởi động.

## Phân tích

Cả bốn file có cùng SHA-256. Phân tích tĩnh bằng Python 3.12 và GNU objdump; không thực thi mẫu.

Strings cho thấy `wpad` ở offset `0x5c832d`. Cần kiểm tra cross-reference để phân biệt tên tiến trình với chuỗi không liên quan.

## Hướng đã thử

Tên calculator ban đầu không phải đáp án: code daemon ghi đè `argv[0]`. Không có bằng chứng sử dụng `prctl(PR_SET_NAME)`; kết luận chỉ áp dụng cho tên dòng lệnh.

## Lời giải

Tại `0xf0f58` code gọi `setsid()`, rồi `chdir()`. Tại `0xf0f7e`, nó nạp địa chỉ `0x5c832d`; tại `0xf0f8a` gọi `strncpy(argv[0], "wpad", strlen(argv[0]))`. Vòng lặp sau đó xóa các đối số còn lại bằng dấu cách.

```bash
objdump -d -M intel --start-address=0xf0f58 --stop-address=0xf0fde files/calculator
```

```python
import argparse, hashlib
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("artifact", type=Path)
a = p.parse_args()
b = a.artifact.read_bytes()
assert hashlib.sha256(b).hexdigest() == "c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6", "Unexpected artifact"
assert b[0xf0f7e:0xf0f85] == bytes.fromhex("488d35a8734d00")
name = b[0x5c832d:].split(b"\0", 1)[0].decode()
print(f"cdctf{{{name}}}")
```

Flag được suy ra và in bởi script cục bộ; chưa có bằng chứng submission được chấp nhận.

## Kết quả

```bash
python exploit.py files/calculator
```

```text
cdctf{wpad}
```

## Tái hiện

```bash
python exploit.py files/calculator
```
