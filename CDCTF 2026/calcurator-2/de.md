# Đề bài - CalcuRATor (2/4)

## Nguyên văn đề

```text
CalcuRATor (2/4)
500
Forensics + Rev Eng
reep236

I decided the best way to understand my sandboxed rootful calculator was to expose it to the internet! When I did, I started noticing some strange packets pouring in, and one of them triggrered some odd behavior! What type of packet does the program respond to?

The flag format is `cdctf{PROTOCOL PACKET TYPE}`, e.g. `cdctf{HTTP GET REQUEST}`, `cdctf{TLS SERVER HELLO}`
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/calculator`, copy từ `C:\Users\Administrator\Downloads\calculator (2)` |
| Kích thước | 7868520 byte |
| SHA-256 | `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6` |
| Loại file | ELF 64-bit little-endian, x86-64 |
| Nhiệm vụ | Tìm loại packet kích hoạt bộ xử lý của backdoor. |

## Hướng giải (tóm tắt)

Tại `0x12b490`, `socket(2,3,1)` tương ứng `AF_INET/SOCK_RAW/IPPROTO_ICMP`. Buffer nhận ở `rsp+0x20`; tại `0x12b4c8`, `[rsp+0x34]` được so với `0x8`. Offset 20 sau IPv4 header là ICMP type, và type 8 là Echo Request.

## Chạy lại lời giải

```bash
python exploit.py files/calculator
```
