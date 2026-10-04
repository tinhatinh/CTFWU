# Đề bài - CalcuRATor (1/4)

## Nguyên văn đề

```text
CalcuRATor (1/4)
491
Forensics + Rev Eng
reep236

My friend recommended me this awesome, open source, command-line calculator. Sadly, I couldn't find it with my package manager, so I downloaded this build online. Something seems off though, because I have to run it as root!

I put the calculator in a sandboxed environment and let it run, but I didn't notice any suspicious listening sockets or unusual processes.

What does the malicious component rename itself to after starting?

The flag format is `cdctf{processname}`
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/calculator`, copy từ `C:\Users\Administrator\Downloads\calculator (1)` |
| Kích thước | 7868520 byte |
| SHA-256 | `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6` |
| Loại file | ELF 64-bit little-endian, x86-64 |
| Nhiệm vụ | Tìm tên mà thành phần độc hại tự đổi thành sau khi khởi động. |

## Hướng giải (tóm tắt)

Tại `0xf0f58` code gọi `setsid()`, rồi `chdir()`. Tại `0xf0f7e`, nó nạp địa chỉ `0x5c832d`; tại `0xf0f8a` gọi `strncpy(argv[0], "wpad", strlen(argv[0]))`. Vòng lặp sau đó xóa các đối số còn lại bằng dấu cách.

## Chạy lại lời giải

```bash
python exploit.py files/calculator
```
