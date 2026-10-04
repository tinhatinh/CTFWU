# notes.md - CalcuRATor (3/4)

## Input

```bash
python -c "from pathlib import Path; import hashlib; b=Path('files/calculator').read_bytes(); print(len(b), hashlib.sha256(b).hexdigest())"
```

Observed: `7868520` bytes, SHA-256 `c89f2641cdedbc1ef041aaeb5b66e821436d99eef40e08087753f9735f3ad3e6`.

## H1 - Triage

Sau kiểm tra type, byte đầu payload phải là `c`; 19 byte tiếp theo đi qua vòng so sánh XOR.

## H2 - Các hướng đã kiểm tra

Chỉ gửi Echo Request chưa đủ: nhánh tại `0x12b4cf` và vòng XOR vẫn từ chối payload không đúng. Chuỗi ở `0x5c62db` cũng không phải khóa plaintext vì byte nhận được bị XOR trước khi so sánh.

Không có thêm thử nghiệm động hoặc nhánh brute-force trong phiên này.

## H3 - Disassembly

```bash
objdump -d -M intel --start-address=0x12b4c8 --stop-address=0x12b5a7 files/calculator
```

Output đã chạy lưu tại `analysis/disassembly.txt`.

Byte payload ở offset 28 phải bằng `0x63`. Vòng lặp `0x12b500` dùng key tại `0x5e700f`, chỉ số 2..20, so với target tại `0x5c62db`, chỉ số 1..19. Phục hồi bằng target XOR key và thêm byte `c` ở đầu. Sau khóa còn cần địa chỉ callback và cổng, đọc bằng `%15s %d`; cổng phải dương và địa chỉ dài ít nhất 7 ký tự để tới nhánh callback.

## H4 - Reproduce

```bash
python exploit.py files/calculator
```

```text
cdctf{1CMP_TR1GG3R$}
```

Output lưu tại `analysis/solve-output.txt`; cờ trong `flag.txt`. Chưa đối chiếu bằng submission.
