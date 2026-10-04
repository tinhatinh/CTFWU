# notes.md - crypto-cat-2

Input: `files/ciphertext.txt` (135 B, sha256 `fc729a7d866ee019d3da211dd885f86922885d6d2205e51e558c1c318c1360dd`), 45 token hex = 45 byte, dải `0x85`-`0xfd`.
Định dạng cờ đề yêu cầu: `cdctf{...}` (theo prefix của các bài CDCTF khác trong cùng giải).

## H1 - Atbash kế thừa từ phần 1
cmd: `python analysis/atbash_check.py` (output: `analysis/atbash_check.out`)
evidence: atbash ở mức ký tự biến chữ số hex thành `0xa2`-`0xab` (ngoài ASCII); bit-NOT ở mức byte
chỉ để lại 11/45 byte trong vùng in được, 6 byte đầu ra `0x13 0x14 0x13 0x04 0x16 0x0b`. Chiếu
nghiệm: cùng bộ đếm chạy với khóa `0x8f` cho 44/45 byte in được cộng 1 ký tự xuống dòng, nên phép
đo có khả năng báo dương chứ không mặc định trả về "rác".
result: DEAD - phần 1 là atbash trên ASCII, bản mã này thao tác ở mức byte.

## H2 - XOR/Vigenère byte nhiều khóa
cmd: `python analysis/triage.py` (output: `analysis/triage.out`)
evidence: chuẩn ASCII tuyệt đối chỉ `xor` sống, mỗi cột 20-94 ứng viên; `sub`/`add` chỉ còn L=8,9,10,15 khi cho phép tab/LF/CR; `beaufort` chết mọi L
result: DEAD - ràng buộc in-được không cắt còn một khóa, không có cách chọn nghiệm.

## H3 - XOR một byte
cmd: `python exploit.py files/ciphertext.txt`
evidence: 0/256 khóa cho ASCII tuyệt đối (vì byte cuối `0x85` buộc plaintext `0x0a`), 5/256 khóa nếu cho phép tab/LF/CR: `0x8c, 0x8f, 0xd9, 0xda, 0xdd`
result: PENDING -> cần crib để tách 1 trong 5.

## H4 - Crib định dạng cờ
cmd: `hit = [k for k in loose if dec(k).startswith(b"cdctf{")]`
evidence: đúng một nghiệm `k = 0x8f`; plaintext `cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}\n`;
mã hóa lại 45 byte với `0x8f` tái tạo đúng chuỗi hex của đề (round-trip True)
result: OK - cờ: `cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
