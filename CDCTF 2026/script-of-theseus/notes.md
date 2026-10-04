# notes.md - script-of-theseus

Input: `files/original_epic_python_script.py` (156 B, sha256 `56c4472cb2f3876c86932bfecb18d276af7f8e8a4b6fb146b40d02d8f90f0b3f`)
Input: `files/replaced_epic_python_script.py` (163 B, sha256 `c88ef02ea2a56fdd9957a86f79d8799fe2b2388a06fe4b9b979f34bbfa402c57`)
Định dạng cờ đề yêu cầu: `cdctf{FF}` với FF là hex in hoa của một byte

## H1 - Nội dung script bị sửa (tên biến, chuỗi, thụt lề)
cmd: `cmp -l files/original_epic_python_script.py files/replaced_epic_python_script.py`
evidence: `cmp: EOF on original after byte 156` rồi hơn 130 dòng lệch, ví dụ `23 12 15`, `68 12 42`.
  Các cặp lệch này không đọc được: một byte chèn ở offset 0x16 làm trôi toàn bộ chỉ số phía sau,
  nên `cmp -l` so hai chuỗi đã lệch pha nhau. Bản này không kết luận được gì.
result: DEAD - `cmp -l` vô dụng khi hai file lệch độ dài, phải đổi sang so theo nội dung đã chuẩn hoá

## H2 - Hai bản giống nhau về text, chỉ khác ký tự xuống dòng
cmd: `sed 's/\r$//' files/replaced_epic_python_script.py > /tmp/theseus/normalized.py && cmp /tmp/theseus/normalized.py files/original_epic_python_script.py`
evidence: `cmp` exit 0, in ra `IDENTICAL after CRLF->LF normalization`. Cùng phép kiểm tra bằng Python:
  `bytes(v for v in b if v != 0x0D) == a` -> `True`.
result: OK - mọi khả năng sửa nội dung (shebang, tên biến, chuỗi, số dòng, thụt lề) bị loại; 7 dòng
  của script vẫn là 7 dòng (`grep -c ''` ra 7 cho cả hai file)

## H3 - Định lượng phần thừa
cmd: `python -c "from collections import Counter; ..."` (đã cố định trong `analysis/byte_freq.py`)
evidence: `original: 156 byte, LF 7, CR 0` / `replaced: 163 byte, LF 7, CR 7`;
  `Them o ban sau : {'0x0D': 7}`, `Mat di o ban sau: {}`.
  Chênh lệch độ dài 7 byte đúng bằng số LF, và LF của hai bên bằng nhau nên phần thừa không phải dòng mới.
result: OK - dẫn sang H4

## H4 - Khác biệt là BOM hoặc encoding
cmd: `file files/*.py` + in 8 byte đầu mỗi file
evidence: bản gốc `23 21 2f 75 73 72 2f 62` (`#!/usr/b`), bản replaced cùng 8 byte đầu; cả hai không có
  `EF BB BF`/`FF FE`/`FE FF`. `file` báo `ASCII text` cho cả hai, chỉ bản replaced có đuôi mô tả
  `with CRLF line terminators`. Số byte không in được cũng tăng đúng 7 (149/156 -> 149/163).
result: DEAD - không có BOM, không đổi mã hoá, chỉ có thêm byte điều khiển

## H5 - Vị trí các byte 0x0D
cmd: `python analysis/byte_freq.py` (xem `analysis/byte_freq.txt`)
evidence: offset `0x16 0x18 0x45 0x63 0x7b 0x82 0xa1`, `Duoc 0x0A di kem: 7/7`.
  16 byte đầu của bản replaced: `23 21 ... 70 79 74 68 6f 6e 33 0d 0a 0d 0a`, tức shebang kết thúc
  bằng `0D 0A` và dòng trống tiếp theo cũng vậy.
result: OK - mỗi lần xuống dòng trong bản replaced là `0D 0A`, bản gốc là `0A`

## H6 - Chốt
cmd: `python exploit.py`
evidence: byte lech duy nhat `0x0D`, 7 lan; xoá 7 byte này thì thu lại 156 byte trùng khớp bản gốc.
  Đề yêu cầu hex in hoa của một byte khác nhau -> `0D`.
result: OK - cờ: `cdctf{0D}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
