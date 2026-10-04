# notes.md - bring-coines

Input: `C:/Users/Administrator/Downloads/bringcoines.exe` (7284057 B, sha256 `576db2ac5c6657189ea446c594092c7b7d0ad5d84f3246b1165d2a372b39c3c6`)
Định dạng cờ đề yêu cầu: `cdctf{...}`
Giải: CDCTF 2026 (Crimson Defense CTF, University of Alabama), Rev Eng, 500 điểm, tác giả adlee7

## H1 - Có payload native đáng phân tích không
cmd: `file bringcoines.exe && r2 -q -c "iS;ii~;ic" bringcoines.exe`
evidence: PE32+ console x86-64, 7 section, `.text` = 0x2dc00 byte trong khi file 7.28 MB. Imports chỉ KERNEL32/USER32 (`GetProcessHeap`, `CreateWindowExW`, `PeekMessageW`, ...), có section `.fptable`.
result: DEAD cho hướng reverse native, nhưng PENDING -> dấu hiệu PyInstaller, chuyển sang H2

## H2 - Đúng là PyInstaller, bản nào, Python nào
cmd: `strings -n 8 bringcoines.exe | grep -iE "pyi|python"` rồi `python -m pyinstxtractor_ng bringcoines.exe`
evidence: chuỗi `PyRun_SimpleStringFlags`, `pyi-python-flag`, `python312.dll`. Tool báo `Pyinstaller version: 2.1+`, `Python version: 3.12`, `Found 21 files in CArchive`, `Found 102 files in PYZ`, entry point `bringcoines.pyc`.
result: OK - mã challenge là `bringcoines.pyc` (3790 B), PYZ chỉ chứa stdlib (argparse, email, csv, socket, ...), không có module tự viết nên không có lớp thứ hai

## H3 - Bỏ qua decompiler, đọc code object trực tiếp
cmd: `python -c "import dis,marshal; dis.dis(marshal.loads(open('bringcoines.pyc','rb').read()[16:]))"`
evidence: magic pyc `cb0d0d0a` = CPython 3.12, máy phân tích chạy 3.12.10 nên `marshal.loads` hoạt động. uncompyle6/decompyle3 không hỗ trợ 3.12.
result: OK - thu được `co_names` = numbers, sys, italics, process_coines, hat_menu, main và toàn bộ hằng số

## H4 - Cờ dựng ở đâu
cmd: xem `hat_menu` trong disassembly (đã lưu `analysis/dis_entry.txt`)
evidence: statement đầu của `hat_menu` là `BUILD_LIST 0` + `LOAD_CONST` tuple 27 số nguyên + `LIST_EXTEND`, tên biến `fleg`. Nhánh `selection == 3` chạy genexpr chỉ có `LOAD_GLOBAL chr` rồi `LOAD_GLOBAL str`, không key, không XOR.
result: OK - `"".join(chr(n) for n in nums)` = `cdctf{h4t_M0us3_p0k3_FLAG!}`

## H5 - Input nào mở được menu
cmd: `grep -n "'\\[(H)34\\]'" analysis/dis_entry.txt`
evidence: `process_coines` so `LOAD_FAST coines_value` với `LOAD_CONST '[(H)34]'` bằng `COMPARE_OP ==`, đúng thì `LOAD_GLOBAL hat_menu`.
result: OK - cổng là chuỗi literal `[(H)34]`, không phải phép tính số nào

## H6 - Nhánh mồi của ô "coins"
cmd: `printf '12345\n' | ./files/bringcoines.exe; printf 'abc\n' | ./files/bringcoines.exe`
evidence: lần lượt in `That's a lotta coines poke. Congrats!` và `That's not coines...` (xem `analysis/decoys.txt`). Giá mũ 2,000 đến 10,000 coins chỉ là chữ, program không giữ số dư.
result: DEAD - cả hai nhánh đều kết thúc mà không tới `hat_menu()`

## H7 - Kiểm chứng cuối
cmd: `printf '[(H)34]\n3\n' | ./files/bringcoines.exe` và `python exploit.py files/bringcoines.exe`
evidence: binary in `Wowee! You want fleg: cdctf{h4t_M0us3_p0k3_FLAG!}` (`analysis/live_run.txt`); script stdlib-only parse cookie `MEI\x0c\x0b\x0a\x0b\x0e` + TOC `>IIIIBc`, lấy entry typecode `s` (pos=22772, stored=1771 B, inflate 3774 B) rồi tự suy ra cùng chuỗi cờ.
result: OK - cờ: `cdctf{h4t_M0us3_p0k3_FLAG!}`

## Bẫy tooling đã gặp
- Console Windows mặc định cp1252: `print` tiếng Việt có dấu trong `exploit.py` bắn `UnicodeEncodeError`. Script phải tự `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`, không dựa vào `PYTHONIOENCODING` của người chạy.
- Payload trong CArchive là marshal thô, **không** có 16-byte pyc header. Header chỉ xuất hiện khi tool ghi ra `.pyc`; cắt nhầm 16 byte của payload thật thì `marshal.loads` báo `ValueError: bad marshal data (unknown type code)`.
- TOC entry là `>IIIIBc` cộng tên pad tới `entry_len` (bắt đầu ở offset 18). Thử layout `>IIIBB` rồi đọc tên từ offset 14 cho ra tên lẫn với byte rác của entry kế trước.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
