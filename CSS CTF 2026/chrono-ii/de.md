# Đề bài - chrono-ii

## Nguyên văn đề

```text
Chrono II
300
Intermediate
We have again intercepted their talk and the cipher text, but this time it seems like its always changing. Help us!

"The Time is ticking, it will never stop, no one will ever decrypt it"

Flag Format: CSSCTF{...}

http://34.116.80.78:8001
```

## Thông tin đã xác minh

| Mục | Giá trị |
| --- | --- |
| Artifact | không có file đề, dữ liệu lấy từ service đang chạy |
| Capture đã lưu | `analysis/rows.txt` (06:38:27-06:39:26), `analysis/feed2.txt` (07:00:51-07:01:50), `analysis/feed3_clean.txt` (07:09:46-07:10:45) |
| Nhiệm vụ | suy lại một plaintext duy nhất từ 60 ciphertext đổi liên tục theo giây |
| Định dạng cờ | `CSSCTF{...}` |
| Đầu mối | Chrono I dùng key là các chữ số của mốc thời gian (Gronsfeld, chu kỳ 14). Bản II giữ đúng ý đó nhưng cho key chạy theo đồng hồ |

## Hướng giải (tóm tắt)

Server mã hoá cùng một plaintext mỗi giây một lần bằng Vigenère. Keystream tuần hoàn chu kỳ 77, dòng tại giây `T` bắt đầu ở chỉ số `43*T mod 77`, và chỉ số này chỉ tiến khi gặp ký tự thực sự bị mã hoá (chữ cái mod 26, chữ số mod 10); `_ { }` đi qua nguyên vẹn và không tiêu tốn key. Sáu ký tự đầu plaintext đã biết là `CSSCTF`, nên mỗi dòng lộ ra 6 symbol của keystream; 120 dòng là khoá đủ 77 symbol với zero conflict.

## Chạy lại lời giải

```bash
python exploit.py analysis/rows.txt analysis/feed2.txt
```

Kết quả: `CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}` (đã lưu trong `flag.txt`).
