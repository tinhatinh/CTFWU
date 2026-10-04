# notes.md - CalcuRATor (2/4)

## Input

```bash
python -c "from pathlib import Path; import hashlib; b=Path('files/calculator').read_bytes(); print(len(b), hashlib.sha256(b).hexdigest())"
```

Observed: `7868520` bytes, SHA-256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`.

## H1 - Triage

Hàm `0x12b460` dùng raw socket. Các hằng số truyền vào socket là 2, 3, 1; byte ICMP type được so với 8.

## H2 - Các hướng đã kiểm tra

HTTP/TLS không phù hợp với hàm đã tìm: socket dùng IPPROTO_ICMP. Echo Request thông thường chỉ vượt qua kiểm tra type, chưa vượt qua kiểm tra khóa.

Không có thêm thử nghiệm động hoặc nhánh brute-force trong phiên này.

## H3 - Disassembly

```bash
objdump -d -M intel --start-address=0x12b460 --stop-address=0x12b536 files/calculator
```

Output đã chạy lưu tại `analysis/disassembly.txt`.

Tại `0x12b490`, `socket(2,3,1)` tương ứng `AF_INET/SOCK_RAW/IPPROTO_ICMP`. Buffer nhận ở `rsp+0x20`; tại `0x12b4c8`, `[rsp+0x34]` được so với `0x8`. Offset 20 sau IPv4 header là ICMP type, và type 8 là Echo Request.

## H4 - Reproduce

```bash
python exploit.py files/calculator
```

```text
cdctf{ICMP ECHO REQUEST}
```

Output lưu tại `analysis/solve-output.txt`; cờ trong `flag.txt`. Chưa đối chiếu bằng submission.
