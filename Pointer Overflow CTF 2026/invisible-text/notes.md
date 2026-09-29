# notes.md - invisible-text

Đầu vào: `files/invisible_text.py` (4245 B, sha256 `f027442b37a521f4a775ec56d37336df446d83e7acd641042e28af030f745320`, khớp card). File sinh riêng cho team: `Content-Disposition` trả về `invisible_text_612.py`.

## Hai tín hiệu nhìn thấy ngay trong file nguồn

- 47/81 dòng kết thúc bằng whitespace. Dòng lẻ (1, 3, 5, ..., 45) có 12 ký tự whitespace (riêng dòng 1 có 10), dòng chẵn chỉ có đúng 1 ký tự tab.
- Chạy script thì nó in ra một bức tranh braille, không in ra chữ nào.

## Vòng giả thuyết

| # | Giả thuyết | Lệnh kiểm tra | Kết quả |
|---|---|---|---|
| H1 | Message nằm trong Unicode vô hình (U+200B..U+200F, U+FEFF, NBSP) | đếm tần suất từng codepoint trên toàn file | **DEAD**: cả file chỉ có 1 ký tự ngoài ASCII, là `—` em dash trong comment |
| H2 | Payload base64 + zlib là nơi cất flag (script là công cụ đọc chính) | `exec` module rồi gọi `_reconstruct()` + `_decode()` | **DEAD**: trả về braille art 33 dòng, 2145 ký tự U+2800-U+28FF, không chứa chữ |
| H3 | Braille art giấu dữ liệu ở số chấm từng ô | histogram của `ord(c) - 0x2800` | **DEAD**: 115 ô = 255 (tròn 8 chấm), 85 ô = 251, 79 ô = 253, 75 ô = 16/4 -> vùng tô đặc của một bức tranh, không phải mã |
| H4 | Whitespace cuối dòng là nhị phân 8 bit nối liền | ghép 299 ký tự whitespace, `space=0/tab=1` và đảo lại, cắt theo 8 bit (kèm cả trường hợp đảo bit) | **DEAD**: cả bốn biến thể ra byte rác, không có `POCTF` |
| H5 | Đây là ngôn ngữ Whitespace (esolang) | tìm LF kết thúc mỗi nhóm và header 3 bit | **DEAD**: không có LF trong nhóm, các nhóm dài cố định 12 ký tự |
| H6 | Mỗi dòng dữ liệu mã hoá một ký tự ASCII 7-bit lấy ở **7 ký tự whitespace cuối cùng** | `bits = tail[-7:]`, `tab=1`, `space=0`, `chr(int(bits,2))` | **OK**: 23 dòng cho 23 ký tự `POCTF{PIEMPAOSMHDLEGRT}` |

## Bằng chứng xác nhận H6

- Ở mọi nhóm 12 ký tự, vị trí thứ 6 luôn là tab, và đó chính là bit đầu của nhóm 7 bit. MSB của mọi ký tự ASCII in được đều bằng 1, nên nhóm 7 bit luôn bắt đầu bằng 1 là dấu hiệu khoá chặt vị trí; 22/22 nhóm cùng trùng một vị trí thì không thể là ngẫu nhiên.
- Số dòng dữ liệu = 23 = độ dài `POCTF{` + 16 + `}`.
- Phần space thừa trước mỗi nhóm (5 space, dòng 1 chỉ còn 3) là padding để căn cột, hai dòng 47 `SS` là phần padding bị cắt.

## Root cause (ghi lại để dùng về sau)

Câu "look in the right place" trong đề trỏ vào **byte thừa cuối dòng**, không phải vào output của script. Thứ tự khám phá hợp lý cho dạng "invisible text": đếm tần suất codepoint vô hình -> quét trailing whitespace -> nhận ra độ dài nhóm cố định -> dùng tính chất MSB của ASCII printable để định vị điểm bắt đầu từng ký tự.

## Nộp flag

```
POST /challenges/invisible-text/submit
{"flag":"POCTF{PIEMPAOSMHDLEGRT}"}
{"correct":true,"message":"Correct."}
```

Server xác nhận đúng và không trả về xâu flag nào khác. `flag.txt` ghi nguyên văn 23 byte thu được từ file.
