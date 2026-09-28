# Đề bài - you cut me off

Ảnh đề bài gốc, chụp từ thẻ challenge:

![de](files/de.png)

## Nguyên văn đề

```text
you cut me off - 491 điểm - oatzs - 87 solves

Here's a flag! It's uhhh ...... ............ ......................uhhhhhhhhhh.....................
hmm.....

File: HEREYOUGO.PNG
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/hereyougo.png` (copy từ: `~/Downloads/hereyougo.png`) |
| Kích thước | 38759 B |
| SHA-256 | xem `flag.txt` bên cạnh, file không đổi: `hereyougo.png` 492x382 RGBA |
| Loại file | PNG ảnh thật, không có metadata, không có chunk ẩn |
| Nhiệm vụ | tìm chuỗi cờ bị "cắt" khỏi ảnh |
| Định dạng cờ | `sun{...}` |

## Hướng giải (tóm tắt)

`IHDR` khai báo chiều cao 382 dòng nhưng chuỗi IDAT giải nén ra đúng 418 dòng scanline
(823042 = 418 x 1969). Trình xem ảnh chỉ vẽ 382 dòng theo header, 36 dòng còn lại vẫn nằm
trong file. Sửa chiều cao dựng lại ảnh đầy đủ thì dòng tin nhắn bị cắt hiện ra, chứa cờ.

## Chạy lại lời giải

```bash
python solve.py
```

Kết quả: `sun{totallyoriginalchallengeidea}` (đã lưu trong `flag.txt`).
