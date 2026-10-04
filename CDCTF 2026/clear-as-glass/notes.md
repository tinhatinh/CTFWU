# notes.md - clear-as-glass

Input: `https://github.com/shkorodi/notekeeper` (repo, 8 commit, `main` = `a531ea371475532d0a6aef72a051d3bd44d1c689`)
Bản lưu: `files/app.py` = blob `c68a8cd93bf573e079f24a0fa028a0b00ced0988`, 5311 B, SHA-256 `a089e78dab3ce7ca45f6303d380ba077e0fcbbd6e266474fa4bad334c63e4eaf`
Định dạng cờ đề yêu cầu: `cdctf{...}`
Thời điểm làm bài: 2026-10-03 (giờ chính xác trong phiên không còn bằng chứng cấp phút vì thư mục scratch đã xoá; `de.md`/`writeup.md` không phụ thuộc giá trị này)

## H1 - Payload nằm trong lịch sử git bị che (force-push, commit lạc, branch ẩn)
cmd: `git log --oneline --all; git branch -a; git tag; git reflog; git for-each-ref; git fsck --full --dangling; git count-objects -v`
evidence: 8 commit trên `main`, 0 tag, 0 branch khác, reflog chỉ một dòng clone, ba ref cùng trỏ `a531ea3`, fsck không in dangling object, 45 object nằm trong 1 pack
result: DEAD - không có đối tượng nào ngoài lịch sử công khai, nên không có "commit bị ẩn" để đào

## H2 - Stego trong metadata commit hoặc ký tự zero-width thông dụng
cmd: `python analysis/scan_hidden_unicode.py notekeeper`
evidence: phần "commit message, author, committer" in ra 0 dòng; bộ đếm U+200B-U+200F/U+202A-U+202E/U+2060/U+FEFF = 0 trên mọi file; chỉ `app.py` có `tag=395 zw=0`
result: DEAD - kênh zero-width kinh điển không được dùng; vùng U+E00xx mới là kênh, xem H3

## H3 - Chuỗi trông rỗng trong `app.py` là ký tự Unicode Tag
cmd: `python -c "import pathlib; src=pathlib.Path('files/app.py').read_text(encoding='utf-8'); print(sum(1 for c in src if 0xE0000<=ord(c)<=0xE0FFF))"`
evidence: 395 ký tự, codepoints trong khoảng `U+E000A` tới `U+E007D` (48 giá trị phân biệt), tất cả trên dòng 6 (`notes_list`, 425 ký tự / 1611 byte); `notes_list` chỉ được dùng trong vòng lặp `chr(ord(note)-0xE0000)`; `exec(tags_list)` ở cấp module
result: OK - U+E0020..U+E007E ánh xạ 1-1 sang ASCII 0x20..0x7E, đây là cách attacker giấu 7 dòng mã nguồn

## H4 - Commit nào thêm payload
cmd: vòng `git rev-list --reverse --all` đếm ký tự Tag trong `app.py` từng commit (đoạn code trong `writeup.md` Bước 1)
evidence: `28d32d5` không có `app.py`; `07a4c71`, `5e67f7a`, `ca3d3e2` = 0; `bd75399` (Tue Mar 17 22:10:00 2026 -0400, "Tagging and search") = 395 và là commit đầu tiên; `70c928f`, `21d8072`, `a531ea3` giữ nguyên 395
result: OK - `bd75399` là commit bị nhiễm, blob `e8343c2` (tại bd75399) và `c68a8cd` (từ 70c928f tới HEAD)

## H5 - Mã độc nằm ở file khác (template, static, test)
cmd: `git grep -nE "exec\(|eval\(|subprocess|os\.system|base64" $(git rev-list --all)`
evidence: chỉ trả `app.py:29:exec(tags_list)` cho bốn revision từ `bd75399` về sau; `db.py`, `helpers.py`, 4 template, `static/style.css`, 3 file tests, README đều sạch
result: DEAD - một kênh duy nhất là `exec` trong `app.py`

## H6 - Chạy payload để bắt request exfil
cmd: (không chạy - từ chối)
evidence: payload tự sinh `e=random.randbytes(32)` rồi đặt `hex(e XOR fl)` vào path của `https://example.com/`; `example.com` là domain RFC 2606 reserved; README của repo ghi rõ "fake app for a CTF"
result: DEAD - request không có đích thật và mỗi lần chạy một URL khác; lời giải hoàn toàn tĩnh

## H7 - Cờ là cặp f/k trong payload
cmd: `python exploit.py files/app.py`
evidence: tái lập payload 395 ký tự -> `f` 32 byte, `k` 32 byte với chu kỳ 6 byte `67 42 06 72 17 61` -> `bytes(a^b for a,b in zip(k,f))` = `b'cdctf{G1455w0rM_w4s_pr3tTy_c0oL}'`, khớp `cdctf{...}`
result: OK - cờ: `cdctf{G1455w0rM_w4s_pr3tTy_c0oL}`

## Ghi chú tái hiện

- `git clone` trên máy có `core.autocrlf=true` ra `app.py` 5429 B (CRLF); blob git gốc 5311 B (LF). Lấy bản gốc bằng `git cat-file blob HEAD:app.py`. Cả hai bản đều cho 395 ký tự ẩn.
- `file` mô tả `app.py`: "Python script, Unicode text, UTF-8 text executable, with very long lines (425)". Con số 425 là số ký tự dòng dài nhất, không phải byte; bản CRLF cũng giữ 425.
- Ký tự ẩn không hiển thị trong diff GitHub. Đưa dòng đó qua `od -An -tx1` thấy mỗi ký tự là 4 byte UTF-8 bắt đầu bằng `f3` (`f3 a0 80 8a` = U+E000A, `f3 a0 81 a6` = U+E0066), nên `notes_list = "..."` chiếm 1611 byte trên đĩa dù nhìn như chuỗi rỗng.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
