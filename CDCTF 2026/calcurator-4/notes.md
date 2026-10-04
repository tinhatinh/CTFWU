# notes.md - CalcuRATor (4/4)

## Input

```bash
python -c "from pathlib import Path; import hashlib; b=Path('files/calculator').read_bytes(); print(len(b), hashlib.sha256(b).hexdigest())"
```

Observed: `7868520` bytes, SHA-256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`.

## H1 - Triage

Strings chứa `libqalculate`, `qalc`, biến môi trường QALCULATE và URL tài liệu. Backdoor có raw ICMP receiver, parser callback và sửa argv.

## H2 - Các hướng đã kiểm tra

Các kết quả tìm kiếm icmpdoor/icmpsh không đủ để kết luận chỉ từ cùng giao thức. Repository JadedWraith được thử nhưng trả HTTP 404. PRISM có đối chiếu cụ thể ở parser và cách đổi tên.

Không có thêm thử nghiệm động hoặc nhánh brute-force trong phiên này.

## H3 - Disassembly

```bash
objdump -d -M intel --start-address=0x12b330 --stop-address=0x12b5a7 files/calculator
```

Output đã chạy lưu tại `analysis/disassembly.txt`.

Repository `Qalculate/libqalculate` chứa CLI qalc. `andreafabrizi/prism` có buffer 1024 byte, ICMP_ECHO, parser `%15s %d`, kiểm tra port > 0 và độ dài IP >= 7, fork rồi reverse shell. Code sửa argv bằng strncpy và memset cũng khớp. Bản challenge đổi tên thành wpad và thêm kiểm tra XOR; tên repository dùng trong flag vẫn là libqalculate/prism.

Nguồn đối chiếu / Source references:

- https://github.com/Qalculate/libqalculate/blob/master/man/qalc.1
- https://github.com/andreafabrizi/prism/blob/master/prism.c


## H4 - Reproduce

```bash
python exploit.py files/calculator
```

```text
cdctf{libqalculate/prism}
```

Output lưu tại `analysis/solve-output.txt`; cờ trong `flag.txt`. Chưa đối chiếu bằng submission.
