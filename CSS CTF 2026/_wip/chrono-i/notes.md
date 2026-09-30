# notes.md - chrono-i

Input: không có artifact. Dữ kiện lấy nguyên văn từ thẻ đề người dùng dán (30/09/2026):
message `2026-09-21 14:35:07 - "As always, The time is always the key to unlock it"`
và ciphertext `ESUITO{gwfvb_xejqnf_nimgt_b_whhrlv}`.
Định dạng cờ đề yêu cầu: `CSSCTF{...}`

## H1 - Thay thế một bảng chữ (monoalphabetic)
cmd: `so sanh CSSCTF -> ESUITO ky tu theo ky tu`
evidence: chữ `S` đứng ở vị trí 2 và 3 của plaintext cho ra `U` rồi `I`. Một bảng chữ
không thể ánh xạ cùng một ký tự thành hai ký tự khác nhau.
result: DEAD - loại ngay, phép mã phụ thuộc vị trí.

## H2 - Hoán vị (transposition)
cmd: `dem da thuc ky tu cua ESUITO so voi CSSCTF`
evidence: `CSSCTF` = {C:2, S:2, T:1, F:1}; `ESUITO` = {E:1, S:1, U:1, I:1, T:1, O:1}.
Hoán vị không đổi đa thức nên không thể ra nhau.
result: DEAD - không phải transpose thuần.

## H3 - Vigenère / Beaufort / variant với crib đã biết
cmd: `python analysis/time_keys.py`
evidence: shift cần cho từng vị trí là `[2,0,2,6,0,9]` (Vigenère), trong khi Beaufort ra
`[6,10,12,10,12,19]` và variant ra `[24,0,24,20,0,17]` - hai cái sau không có cấu trúc
nào đọc được. Chuỗi Vigenère lại chính là 6 chữ số đầu của `20260921143507`, tức
message `2026-09-21 14:35:07` bỏ ký tự phân cách. Script thử 95 cách sinh key từ mốc
thời gian (epoch giây theo UTC/UTC+7/AEST/EDT, cumulative sum, cặp hai chữ số, cơ số 26
MSB và LSB, hex, từng trường ngày-giờ nhân chỉ số...); chỉ ba nguồn khớp và cả ba đều là
dãy chữ số của `20260921...`.
result: PENDING -> chốt ở H4.

## H4 - Dem key chay theo chu cai hay theo moi ky tu
cmd: `python analysis/decrypt.py`
evidence: đếm chỉ trên chữ cái cho `CSSCTF{every_second_hides_a_secret}`; đếm trên mọi
ký tự (kể cả `{` và `_`) cho `CSSCTF{fvbsw_qcjohf_lhlcq_b_uhfllm}`.
result: OK - key `20260921143507` lặp chu kỳ 14, bộ đếm chỉ tiến khi gặp chữ cái.

## H5 - Nghi ngờ key 14 chữ số chỉ khớp 6 ký tự đầu do trung hop
cmd: `python exploit.py` (ba bien the)
evidence: bien the `...whhrlW` -> than co `every_second_hides_a_secreU`, bi chang
`[a-z0-9_]*` chan lai; doi gio trong message thanh `15:35:07` -> crib lech ngay ky tu
thứ ba, dung o buoc doi khop key; doi prefix `ESUITO` thanh `XSUITO` -> cung dung o
buoc do. Tuc la ba lop kiem tra deu that, khong phai vong lap.
result: OK - cờ: `CSSCTF{every_second_hides_a_secret}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
