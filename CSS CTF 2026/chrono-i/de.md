# Đề bài - chrono-i

## Nguyên văn đề

```text
Chrono I
75
Beginner
We have intercepted a message and a Ciphertext, please help us crack the Ciphertext!

Message:

2026-09-21 14:35:07 - "As always, The time is always the key to unlock it"

Ciphertext:

ESUITO{gwfvb_xejqnf_nimgt_b_whhrlv}

Flag Format: CSSCTF{...}
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Nguồn | Thẻ đề do người dùng dán trong phiên, 30/09/2026 (không có file đính kèm) |
| Giải | CSS CTF 2026: Return of Nexus |
| Điểm / độ khó | 75 / Beginner |
| Artifact | không có - dữ kiện nằm hết trong thẻ đề |
| Nhiệm vụ | thu được `CSSCTF{...}` từ `ESUITO{...}` |
| Định dạng cờ | `CSSCTF{...}` |
| Trạng thái nộp | cờ kiểm chứng cục bộ (mã hoá ngược ra đúng ciphertext gốc); chưa có xác nhận đã được chấm chấp nhận |

Hai dữ kiện đề cho thẳng: prefix cờ đã biết (`CSSCTF`) và một mốc thời gian
`2026-09-21 14:35:07` được nói là "the key".

## Hướng giải (tóm tắt)

Crib `CSSCTF` -> `ESUITO` cho ra đúng sáu chữ số `2 0 2 6 0 9`, tức six first digits của
`20260921143507` - chuỗi số lấy từ mốc thời gian trong đề. Mã là Gronsfeld (Vigenère số)
chu kỳ 14, key chạy theo thứ tự chữ cái còn `{`, `}`, `_` giữ nguyên. Giai mã phần thân
thì ra `CSSCTF{every_second_hides_a_secret}`.

## Chạy lại lời giải

```bash
python exploit.py
```

Kết quả: `CSSCTF{every_second_hides_a_secret}` (đã lưu trong `flag.txt`).
