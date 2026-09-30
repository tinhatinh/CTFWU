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

## Thông tin đã xác minh

| Mục | Giá trị |
| --- | --- |
| Nguồn | Thẻ đề do người dùng dán trong phiên, 30/09/2026 (không có file đính kèm) |
| Giải | CSS CTF 2026: Return of Nexus |
| Điểm / độ khó | 75 / Beginner |
| Artifact | không có — dữ kiện nằm hết trong thẻ đề |
| Nhiệm vụ | thu được `CSSCTF{...}` từ `ESUITO{...}` |
| Định dạng cờ | `CSSCTF{...}` |

Hai dữ kiện đề cho thẳng: prefix cờ đã biết (`CSSCTF`) và một mốc thời gian
`2026-09-21 14:35:07` được nói là "the key".

## Hướng giải (tóm tắt)

Vigenère nhiều bảng chữ, key sinh từ mốc thời gian. Phá bằng cách brute-force
cách diễn giải chuỗi thời gian (epoch giây, các trường ngày-giờ, tổng chữ số
lũy tiến, ...) trên crib `CSSCTF` -> `ESUITO`, rồi kiểm phần còn lại đọc ra
tiếng Anh.

## Chạy lại lời giải

```bash
python exploit.py
```

Kết quả: `CSSCTF{...}` (đã lưu trong `flag.txt`).
