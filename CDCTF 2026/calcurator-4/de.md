# Đề bài - CalcuRATor (4/4)

## Nguyên văn đề

```text
CalcuRATor (4/4)
500
Forensics + Rev Eng + OSINT
reep236

The owner of the sketchy site seems to only host builds based on open-source software, so maybe he hybridized it with another tool to mess around on my system... can you figure out which two programs he merged together?

The flag format is `cdctf{calculator/tool}`

An example flag for two projects who's source repositories are of the form "https://repo.com/repos/mycalculator.git" and "https://source.net/sources/mytool.git" would be `cdctf{mycalculator/mytool}`
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/calculator`, copy từ `C:\Users\Administrator\Downloads\calculator (4)` |
| Kích thước | 7868520 byte |
| SHA-256 | `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6` |
| Loại file | ELF 64-bit little-endian, x86-64 |
| Nhiệm vụ | Xác định hai repository nguồn của calculator và backdoor. |

## Hướng giải (tóm tắt)

Repository `Qalculate/libqalculate` chứa CLI qalc. `andreafabrizi/prism` có buffer 1024 byte, ICMP_ECHO, parser `%15s %d`, kiểm tra port > 0 và độ dài IP >= 7, fork rồi reverse shell. Code sửa argv bằng strncpy và memset cũng khớp. Bản challenge đổi tên thành wpad và thêm kiểm tra XOR; tên repository dùng trong flag vẫn là libqalculate/prism.

## Chạy lại lời giải

```bash
python exploit.py files/calculator
```
