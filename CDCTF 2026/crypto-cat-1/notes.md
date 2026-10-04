# notes.md - crypto-cat-1

Input: `files/ciphertext.txt` (30 B gồm newline, 29 ký tự ciphertext, sha256 `901d528d70490f20879dbbf29865c48c3440647a156e57ae261201f0db39cf99`)
Định dạng cờ: `cdctf{...}` (xác nhận từ chính lời giải, các bài CDCTF khác trong giải dùng cùng prefix)

## H1 - XOR một byte (theo đúng tên bài "xor with many keys")
cmd: `python exploit.py files/ciphertext.txt` (đoạn dò 256 khoá)
evidence: 16/256 khoá cho output nằm trong dải ASCII in được, ví dụ `0x01 -> yvyftz{fx{ir0l^sf^gj^sl^r2hw|`, `0x1b -> clc|n`a|bash*vDi|D}pDivDh(rmf`. Chỉ `0x00` giữ được `{` tại chỉ số 5, tức không mã hoá.
result: DEAD - không khoá nào cho chuỗi đọc được; tên "xor with many keys" trong đề mô tả khoá master của phần 5, không phải minor key này.

## H2 - Vigenere/Beaufort với khoá lấy từ tên nhân vật
cmd: `python -c` với key `caticus`, giải cả hai chiều:
`enc[i] = (plain[i] + key[i]) mod 26` và `enc[i] = (key[i] - plain[i]) mod 26`
evidence: ra `lmuoi{xuowpg1k_hd_tg_fc_a3et}` (Vigenere) và `edvbh{svbtaj1f_im_wj_kn_p3lw}`
(Beaufort). Cả hai đều có 5 ký tự đầu rác, trong khi `{` vẫn ở chỉ số 5 - đúng như
dự đoán vì chỉ chữ cái bị biến đổi.
result: DEAD - prefix không khớp `cdctf`, và chọn khoá theo tên nhân vật chỉ là phỏng đoán.

## H3 - Caesar (dịch chuyển cố định cho mọi chữ cái)
cmd: `python analysis/triage.py`
evidence: bảng 25 dịch chuyển được in đầy đủ. Không dòng nào có 5 ký tự đầu là một flag tag, ví dụ `+13 -> kjkth{mtlmuf1z_et_sx_ez_f3vi}`, `+20 -> rqrao{tastbm1g_la_ze_lg_m3cp}`.
result: DEAD - loại toàn bộ 25 khả năng.

## H4 - Atbash (a<->z) vì `{`, `_`, số giữ nguyên vị trí
cmd: `python analysis/triage.py` (dòng cuối) rồi `python exploit.py files/ciphertext.txt`
evidence: `xwxgu` -> `cdctf` khớp prefix cờ của giải; toàn chuỗi -> `cdctf{atbash1n_it_up_in_h3re}`; `atbash(atbash(cipher)) == cipher` (hàm là involution, được assert trong exploit).
result: OK - cờ: `cdctf{atbash1n_it_up_in_h3re}`

## Còn mở
Bốn minor key đều cần cho phần 5 ("xor with many keys" trên khoá master). Giữ lại flag từng phần.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
