# notes.md - CalcuRATor (1/4)

## Input

```bash
python -c "from pathlib import Path; import hashlib; b=Path('files/calculator').read_bytes(); print(len(b), hashlib.sha256(b).hexdigest())"
```

Observed: `7868520` bytes, SHA-256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`.

## H1 - Triage

Strings cho thấy `wpad` ở offset `0x5c832d`. Cần kiểm tra cross-reference để phân biệt tên tiến trình với chuỗi không liên quan.

## H2 - Các hướng đã kiểm tra

Tên calculator ban đầu không phải đáp án: code daemon ghi đè `argv[0]`. Không có bằng chứng sử dụng `prctl(PR_SET_NAME)`; kết luận chỉ áp dụng cho tên dòng lệnh.

Không có thêm thử nghiệm động hoặc nhánh brute-force trong phiên này.

## H3 - Disassembly

```bash
objdump -d -M intel --start-address=0xf0f58 --stop-address=0xf0fde files/calculator
```

Output đã chạy lưu tại `analysis/disassembly.txt`.

Tại `0xf0f58` code gọi `setsid()`, rồi `chdir()`. Tại `0xf0f7e`, nó nạp địa chỉ `0x5c832d`; tại `0xf0f8a` gọi `strncpy(argv[0], "wpad", strlen(argv[0]))`. Vòng lặp sau đó xóa các đối số còn lại bằng dấu cách.

## H4 - Reproduce

```bash
python exploit.py files/calculator
```

```text
cdctf{wpad}
```

Output lưu tại `analysis/solve-output.txt`; cờ trong `flag.txt`. Chưa đối chiếu bằng submission.
