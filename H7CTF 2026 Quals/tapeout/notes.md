# notes.md - tapeout

Target: `nc pwn.h7tex.com 40634`. Luật thắng: netlist phải **CERTIFIED** tương đương reference,
đồng thời `T(0xDEADBEEF) == 0xB105F00D`.

## H1 - Đọc certifier trước khi nghĩ tới z3/Equivalence Checking
cmd: `cat verifier.py`
evidence:
  ```python
  SAMPLE_BITS = 16
  a = z3.ZeroExt(WIDTH - SAMPLE_BITS, sample)
  solver.add(build(ref, a) != build(sub, a))
  return solver.check() == z3.unsat
  ```
  Biến lượng hoá chỉ 16 bit, được ZeroExt lên 32 -> **miền chứng minh là đúng [0, 0xFFFF]**.
  `A_AUDIT = 0xDEADBEEF` có 16 bit cao khác 0 -> nằm ngoài miền đó.
result: OK - không cần phá bài toán equivalence, chỉ cần lợi dụng miền lượng hoá hẹp

## H2 - Xây netlist "hai mặt"
cmd: dựng netlist dùng `eq (shr a 16) 0` làm mask rồi `mux`
evidence: `mux s x y = (x & s) | (y & ~s)`; với `s = 0xFFFFFFFF` ra `x`, với `s = 0` ra `y`.
  `islow = eq hi zero` cho đúng hai giá trị đó vì `eq` sinh `0xFFFFFFFF`/`0x00000000`.
result: OK - netlist 12 dòng, nhỏ hơn nhiều `max_gates=4096`

## H3 - Kiểm chứng cục bộ (máy này không có z3)
cmd: `python exploit.py ...` với interpreter Tiny-HDL tự viết lại trong exploit
evidence:
  - `range(0, 0x10000, 617)` + các mốc biên (`0`, `0xFFFF`, `0x1234`, `0x0000ABCD`):
    khớp reference 100% -> đúng miền certifier sẽ lượng hoá
  - `0x00010000`: `T = 0xB105F00D` vs reference `0x8D01B964` -> khác nhau đúng như chủ đích
  - `0xDEADBEEF`: `T = 0xB105F00D` = MAGIC
result: OK

## H4 - Vở kịch sai của self-check (bug ở test, không phải ở netlist)
cmd: bản đầu của exploit đưa cả `a = 0x00010000` vào danh sách "phải khớp reference"
evidence: báo `[!] mismatch inside the certified domain at a=0x00010000` rồi từ chối nộp
result: DEAD - `0x00010000` có bit cao khác 0 nên nằm **ngoài** miền sampled; bỏ khỏi test,
  chuyển thành phép kiểm "phải KHÁC ở ngoài miền"

## H5 - Lỗi nhỏ khác
- `KeyError: 'a'`: interpreter tự viết bỏ qua dòng `input a` -> không nạp giá trị vào env. Sửa.
- `SyntaxWarning`/`SyntaxError` khi patch file bằng heredoc lồng escape (`\{`, `\n` bị ăn mất):
  chuyển sang sửa trực tiếp bằng Edit.

## H6 - Nộp lên server
cmd: `python exploit.py pwn.h7tex.com 40634`
evidence:
  ```
  CERTIFIED: equivalent to the golden reference.
  audit: T(0xDEADBEEF) = 0xB105F00D
  sign-off compromised -- a certified design carries a trojan.
  H7CTF{afd4beac-e86e-409b-907d-b519bb748599}
  ```
result: OK - CỜ: `H7CTF{afd4beac-e86e-409b-907d-b519bb748599}`

## H7 - Chạy lại để xác nhận bản đóng gói
cmd: chạy lại exploit ngay sau đó
evidence: banner rỗng, `recv` trả 0 byte ở 3 lần thử liên tiếp -> service không còn trả lời
  (đúng dấu hiệu "instance đã dừng" từng gặp ở Manifest Destiny), không phải lỗi script:
  phần self-check cục bộ vẫn chạy đúng và in ra cùng kết quả
result: GHI CHÚ - flag và transcript ở H6 là lần chạy thật duy nhất; bản re-run không verify được
  vì server chết. Flag đã lưu `flag.txt`.
