# Đề bài - CalcuRATor (3/4)

## Nguyên văn đề

```text
CalcuRATor (3/4)
500
Forensics + Rev Eng
reep236

Sadly when I send this packet, the sandboxed exposed rootful calculator does not behave any differently. What key piece of information am I missing?

The flag format is `cdctf{Fl4g!}`
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/calculator`, copy từ `C:\Users\Administrator\Downloads\calculator (3)` |
| Kích thước | 7868520 byte |
| SHA-256 | `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6` |
| Loại file | ELF 64-bit little-endian, x86-64 |
| Nhiệm vụ | Khôi phục thông tin còn thiếu trong payload của ICMP Echo Request. |

## Hướng giải (tóm tắt)

Byte payload ở offset 28 phải bằng `0x63`. Vòng lặp `0x12b500` dùng key tại `0x5e700f`, chỉ số 2..20, so với target tại `0x5c62db`, chỉ số 1..19. Phục hồi bằng target XOR key và thêm byte `c` ở đầu. Sau khóa còn cần địa chỉ callback và cổng, đọc bằng `%15s %d`; cổng phải dương và địa chỉ dài ít nhất 7 ký tự để tới nhánh callback.

## Chạy lại lời giải

```bash
python exploit.py files/calculator
```
