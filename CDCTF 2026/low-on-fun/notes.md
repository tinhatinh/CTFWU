# notes.md - Low on function names

Input: `files/low_on_fun.py` (8690 B, sha256 `cb043a7dc96d316c7e46825268511bf5b0c2da38599ede991af237ccb7edff5f`)
Định dạng cờ đề yêu cầu: `cdctf{ex4mpl3_fl4g}`

## H1 - Đọc code object bằng Python hệ thống 3.12
cmd: `py -3.12 analysis/dump_dis.py 2`
evidence: phần 2 dài 850 byte giải mã thành `POP_JUMP_IF_NOT_NONE 0` tại offset 0 rồi chết với `IndexError: tuple index out of range`; phần 0 dài 28 byte cũng bắt đầu bằng cùng opcode vô lý. Chuỗi lệnh lệch khung cache nên opcode bị đọc sai hàng loạt.
result: DEAD - bytecode không thuộc 3.12, mọi kết luận từ disassembly này vô giá trị.

## H2 - Thử lại với Python 3.11
cmd: `py -3.11 analysis/dump_dis.py 0`
evidence: cùng dấu hiệu, offset 0 là `POP_JUMP_FORWARD_IF_NOT_NONE`, `LIST_TO_TUPLE` và `BEFORE_ASYNC_WITH` xuất hiện trong một hàm chỉ chứa `input()`.
result: DEAD - vẫn sai version.

## H3 - Chạy trực tiếp file đề trên từng interpreter có máy
cmd: `bash analysis/run_triage.sh`
evidence: `py -3.9` báo `ValueError: bad marshal data (unknown type code)`; `py -3.11` và `py -3.12` segfault (exit 139) vì `marshal.loads` ACCEPT cấu trúc code object nhưng interpreter đi thực thi với layout cache của phiên bản khác; `py -3.14` in ra đúng prompt và `That's the wrong length!`.
result: PENDING -> mục tiêu là CPython 3.14, mọi phân tích phải làm trên 3.14.

## H4 - Coi checker là oracle và brute-force
cmd: `py -3.14 files/low_on_fun.py` với các đầu vào thử
evidence: checker chỉ trả về đúng một trong hai chuỗi `b"That's it!"` hoặc `b'heck nah'` sau khi so sánh cả 40 byte, không có so sánh từng ký tự và không có tín hiệu thời gian tách theo byte.
result: DEAD - không cần thiết, xem H5: keystream không phụ thuộc plaintext nên suy ngược trực tiếp được.

## H5 - Chuỗi lệnh 3.14 của phần thứ ba (checker)
cmd: `py -3.14 analysis/dump_dis.py 2`
evidence: `key = bytes.fromhex(<256 ký tự hex>)` (128 byte); `enc = [36 hằng số hex]` nhưng `LIST_APPEND` chạy 40 lần với các chỉ số 5, 11, 14 bị dùng lại; `check = bytes.fromhex(''.join(enc))` (40 byte); `S = list(range(256))` cùng vòng KSA `j = (S[i] + j + key[i % key_length]) % 256`, rồi vòng PRSA `keystream_byte = S[(S[k] + S[l]) % 256]`, `out.append(byte ^ keystream_byte)`, cuối cùng `if bytes(out) == check`. Đây là RC4 nguyên bản.
result: PENDING -> xác nhận ở H6.

## H6 - Suy ngược RC4 và kiểm chứng
cmd: `python exploit.py files/low_on_fun.py`
evidence: `check = 612eba336f913337b3de4c3b1e03f199014c12084a93e3f847d4bea54c03517f1bdc2718cc2d6cfb` (40 byte) XOR keystream -> `cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}`; độ dài 40 khớp `len(inp) == 40` của `init_checks`, prefix `cdctf` khớp `startswith('cdctf')`. Chạy lại bằng chính checker gốc: bản đầy đủ in `That's it!`, bản đổi ký tự cuối `k` -> `l` in `heck nah`.
result: OK - cờ: `cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
